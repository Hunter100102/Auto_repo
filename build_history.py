"""Index Katy's messages in one bot-accessible channel without AI calls."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
katy = os.environ["KATY_SLACK_USER_ID"]
channel_id = os.environ["HISTORY_CHANNEL_ID"]
out = Path("data/history.jsonl")
out.parent.mkdir(exist_ok=True)

records = []
cursor = None
try:
    while True:
        options = {"channel": channel_id, "limit": 100}
        if cursor:
            options["cursor"] = cursor
        page = client.conversations_history(**options)
        for message in page.get("messages", []):
            text = message.get("text", "").strip()
            if message.get("user") == katy and len(text) >= 8 and not message.get("bot_id"):
                records.append({"channel": channel_id, "ts": message["ts"], "text": text})
        cursor = page.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
except Exception as exc:
    print(f"History build failed for channel {channel_id}: {exc}")
    raise SystemExit(1)

# A failed scan never overwrites an existing index.
with out.open("w", encoding="utf-8") as file:
    for record in records:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
print(f"Indexed {len(records)} Katy messages from {channel_id} to {out}")
