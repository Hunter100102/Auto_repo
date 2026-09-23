import json, os, time
from pathlib import Path
from dotenv import load_dotenv
from slack_sdk import WebClient
load_dotenv()
from ai import embed
client=WebClient(token=os.environ['SLACK_BOT_TOKEN'])
katy=os.environ['KATY_SLACK_USER_ID']
out=Path('data/history.jsonl'); out.parent.mkdir(exist_ok=True)

def pages(method, **kwargs):
    cursor=None
    while True:
        r=method(limit=200, cursor=cursor, **kwargs)
        yield r
        cursor=r.get('response_metadata',{}).get('next_cursor')
        if not cursor: break

records=[]
# Bot-visible conversations only. Invite the bot to channels whose history should be learned.
for pg in pages(client.conversations_list, types='public_channel,private_channel', exclude_archived=True):
    for ch in pg['channels']:
        cid=ch['id']
        try:
            for hp in pages(client.conversations_history, channel=cid):
                for m in hp['messages']:
                    txt=m.get('text','').strip()
                    if m.get('user')==katy and len(txt)>=8 and not m.get('bot_id'):
                        records.append({'channel':cid,'ts':m['ts'],'text':txt,'embedding':embed(txt)})
        except Exception as e:
            print('Skipping',cid,e)
with out.open('w',encoding='utf-8') as f:
    for r in records: f.write(json.dumps(r,ensure_ascii=False)+'\n')
print(f'Indexed {len(records)} Katy messages to {out}')
