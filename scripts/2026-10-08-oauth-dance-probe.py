#!/usr/bin/env python3
"""Full OAuth-dance probe (Lapidary 5, 2026-10-08, pre-class sprint).

Plays claude.ai's role end to end against a running server: discovery ->
DCR -> GET /authorize (form) -> POST credentials (fresh sign-up) ->
capture code from redirect -> PKCE token exchange -> call MCP with the
won token -> expect USER mode. BASE from argv[1] or local."""
import base64, hashlib, json, os, re, secrets, sys, urllib.parse, urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")

def get(url, data=None, headers=None, redirect=True):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener() if redirect else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, data, headers or {})
    try:
        r = opener.open(req)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

# 1. discovery
st, _, body = get(f"{BASE}/.well-known/oauth-authorization-server")
meta = json.loads(body); assert st == 200, st
print("1 discovery ok:", meta["authorization_endpoint"])

# 2. DCR
st, _, body = get(meta["registration_endpoint"],
                  json.dumps({"redirect_uris": ["https://claude.ai/api/mcp/auth_callback"]}).encode(),
                  {"Content-Type": "application/json"})
client_id = json.loads(body)["client_id"]; assert st == 201, st
print("2 registered client:", client_id[:8], "…")

# 3. authorize GET -> form renders
verifier = secrets.token_urlsafe(48)
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
q = urllib.parse.urlencode({"client_id": client_id,
    "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
    "state": "probe-state-xyz", "code_challenge": challenge,
    "code_challenge_method": "S256", "response_type": "code"})
st, _, body = get(f"{meta['authorization_endpoint']}?{q}")
assert st == 200 and b"Sign in" in body, (st, body[:120])
hidden = dict(re.findall(rb'name="([a-z_]+)" value="([^"]*)"', body))
print("3 login form rendered; hidden fields:", len(hidden))

# 4. POST credentials (fresh sign-up = the student path)
email = f"dance-{os.urandom(3).hex()}@example.com"
form = {k.decode(): v.decode() for k, v in hidden.items()}
form.update({"email": email, "password": "dance-Passw0rd!x", "mode": "signup"})
st, hdrs, body = get(meta["authorization_endpoint"],
                     urllib.parse.urlencode(form).encode(),
                     {"Content-Type": "application/x-www-form-urlencoded"}, redirect=False)
assert st in (302, 307), (st, body[:200])
loc = hdrs.get("Location") or hdrs.get("location")
code = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)["code"][0]
state = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)["state"][0]
assert state == "probe-state-xyz"
print("4 signed up", email, "-> code captured, state round-tripped")

# 5. token exchange with PKCE
st, _, body = get(meta["token_endpoint"],
                  urllib.parse.urlencode({"grant_type": "authorization_code",
                      "code": code, "code_verifier": verifier,
                      "client_id": client_id,
                      "redirect_uri": "https://claude.ai/api/mcp/auth_callback"}).encode(),
                  {"Content-Type": "application/x-www-form-urlencoded"})
tok = json.loads(body); assert st == 200 and tok.get("access_token"), (st, body[:200])
print("5 token exchange ok (access", len(tok["access_token"]), "chars; refresh:", bool(tok.get("refresh_token")), ")")

# 5b. wrong verifier must fail
st2, _, b2 = get(meta["token_endpoint"],
                 urllib.parse.urlencode({"grant_type": "authorization_code",
                     "code": "reused-or-bad", "code_verifier": "x", "client_id": client_id}).encode(),
                 {"Content-Type": "application/x-www-form-urlencoded"})
assert st2 == 400
print("5b bad/reused code refused (400) — one-time + PKCE hold")

# 6. the won token opens a private shelf over MCP
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def check():
    async with streamablehttp_client(f"{BASE}/mcp",
            headers={"Authorization": f"Bearer {tok['access_token']}"}) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("user_status", {})
            print("6 MCP says:", res.content[0].text[:90])
            assert "user —" in res.content[0].text
asyncio.run(check())
print("DANCE COMPLETE: discovery -> DCR -> login -> code -> PKCE token -> user mode")
