# Katy Slack Assistant

A conservative Slack assistant that:
1. Watches DMs to the app and @mentions of the app.
2. Searches a local archive of Katy's prior Slack replies for semantically similar answered questions.
3. If a strong prior answer exists, drafts a concise response grounded only in Katy's prior answer.
4. Otherwise sends a generic acknowledgment promising an update by end of day.
5. Adds every unresolved request to a local follow-up queue.
6. Sends Katy a 2:30 PM America/New_York digest of unresolved follow-ups.

## Important Slack limitation
A Slack app cannot automatically read "all channels" merely because you have an API key. Access is controlled by OAuth scopes, workspace/admin policy, channel membership, and channel type. For a safe first release, invite the bot to the channels it should read and use its message-history scopes. Private channels require explicit access. DMs between Katy and other people are not automatically visible to a bot unless the workspace/app permissions and Slack API mode permit it.

## Setup
1. Create a Slack app at api.slack.com/apps -> Create New App -> From scratch.
2. Add a bot user.
3. OAuth & Permissions -> Bot Token Scopes:
   - app_mentions:read
   - channels:history
   - channels:read
   - groups:history
   - groups:read
   - im:history
   - im:read
   - mpim:history
   - mpim:read
   - chat:write
   - users:read
4. Install/reinstall the app to the workspace. An admin may need to approve it.
5. Enable Socket Mode and create an App-Level Token with `connections:write`.
6. Event Subscriptions -> subscribe to bot events:
   - app_mention
   - message.im
   Add message.channels/message.groups only if you intentionally want the app to observe every message in channels it can access; this starter intentionally reacts only to direct requests/mentions.
7. Invite the bot to every public/private channel whose history it may use.
8. Copy `.env.example` to `.env`, add tokens, Katy's Slack user ID, and an OpenAI API key.
9. `python -m venv .venv`
10. Windows: `.venv\\Scripts\\activate`; macOS/Linux: `source .venv/bin/activate`
11. `pip install -r requirements.txt`
12. First build Katy's historical response index: `python build_history.py`
13. Review `data/history.jsonl` for obviously bad/sensitive examples.
14. Test without sending: set `AUTO_SEND=false` and run `python app.py`.
15. When satisfied, set `AUTO_SEND=true` and restart.

## How matching works
`build_history.py` scans channels the bot can access and stores messages authored by Katy. `app.py` uses embeddings to retrieve similar prior messages, then asks the LLM to determine whether a retrieved message actually answers the new request. The LLM is forbidden from inventing facts. If no safe answer is found, it sends only an acknowledgment and creates a follow-up.

## Recommended production change
Start with `AUTO_SEND=false` for a short test against a private sandbox channel. Then enable sending. Do not expose Slack/OpenAI tokens in Git. Use Render/Railway/Fly/your server environment variables in production.
