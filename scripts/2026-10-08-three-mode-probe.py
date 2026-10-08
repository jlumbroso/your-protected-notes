#!/usr/bin/env python3
"""Three-mode probe for your-protected-notes (Lapidary 5, 2026-10-08).

Proves the full HTTP path, not the mechanism: (1) sign-up via Stack's
client REST (the same door a student uses) -> access token; (2) MCP
session WITHOUT auth header -> guest mode, note lands on the commons;
(3) MCP session WITH Bearer token -> user mode, note lands on a private
shelf invisible to the guest; (4) garbled token -> loud error (ADR-0004).
Run with server env already exported; server assumed on :8000.
"""
import asyncio, json, os, sys, urllib.request

PROJECT = os.environ["STACK_PROJECT_ID"]
PUB_KEY = os.environ["STACK_PUB_CLIENT_KEY"]
BASE = "http://127.0.0.1:8000/mcp"

def stack(path, payload):
    req = urllib.request.Request(
        f"https://api.stack-auth.com/api/v1{path}",
        json.dumps(payload).encode(),
        {"Content-Type": "application/json",
         "X-Stack-Project-Id": PROJECT,
         "X-Stack-Publishable-Client-Key": PUB_KEY,
         "X-Stack-Access-Type": "client"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

async def session(headers, label, calls):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(BASE, headers=headers) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            out = []
            for tool, args in calls:
                res = await s.call_tool(tool, args)
                text = res.content[0].text if res.content else "(no content)"
                print(f"[{label}] {tool}: {text[:140]}")
                out.append((bool(getattr(res, "isError", False)), text))
            return out

async def main():
    email = f"probe-{os.urandom(3).hex()}@example.com"
    up = stack("/auth/password/sign-up", {"email": email, "password": "probe-Passw0rd!x", "verification_callback_url": "http://localhost/dev-null"})
    token = up["access_token"]
    print(f"signed up {email}; token acquired ({len(token)} chars)")

    await session({}, "guest", [
        ("user_status", {}),
        ("add_note", {"note": "guest commons note from the probe"}),
        ("list_notes", {}),
    ])
    await session({"Authorization": f"Bearer {token}"}, "user ", [
        ("user_status", {}),
        ("add_note", {"note": "private shelf note from the probe"}),
        ("list_notes", {}),
    ])
    await session({}, "guest2", [("list_notes", {})])  # must NOT see the private note
    try:
        out = await session({"Authorization": "Bearer garbage.token.here"}, "bad  ", [("user_status", {})])
        is_err, text = out[0]
        if is_err or text.startswith("Error"):
            print("[bad  ] loud failure as designed (tool error, not silent guest) — ADR-0004 holds")
        else:
            print("[bad  ] ADR-0004 VIOLATED: invalid token answered as", text[:60])
    except Exception as e:
        print(f"[bad  ] loud failure as designed (transport): {type(e).__name__}")

asyncio.run(main())

# OUTCOME (2026-10-08, first live run): all four behaviors proven against
# real Stack sign-up + real JWT on project winter-block-03155413 —
# guest commons (PBKK/QWG0), private shelf (KXMB) invisible to guest2,
# email displayed from users_sync, garbled token -> loud tool error
# (ADR-0004 holds; the probe initially misread tool-errors as success).
