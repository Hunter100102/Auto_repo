import logging
import os, re
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
load_dotenv()
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from apscheduler.schedulers.background import BackgroundScheduler
from ai import retrieve, generate
from store import seen, mark, add_followup, open_followups

BOT_TOKEN=os.environ['SLACK_BOT_TOKEN']; APP_TOKEN=os.environ['SLACK_APP_TOKEN']; KATY=os.environ['KATY_SLACK_USER_ID']
TZ=os.getenv('TIMEZONE','America/New_York'); AUTO=os.getenv('AUTO_SEND','false').lower()=='true'; TH=float(os.getenv('MIN_MATCH_SCORE','0.35'))
app=App(token=BOT_TOKEN); client=WebClient(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger=logging.getLogger(__name__)

def username(uid):
    try: return client.users_info(user=uid)['user']['profile'].get('first_name') or client.users_info(user=uid)['user'].get('real_name') or 'there'
    except: return 'there'

def handle(event):
    uid=event.get('user'); text=event.get('text','').strip(); channel=event.get('channel'); ts=event.get('ts')
    if not uid or uid==KATY or not text or event.get('bot_id'): return
    key=f'{channel}:{ts}'
    if seen(key): return
    # Remove bot mention before retrieval.
    clean=re.sub(r'<@[A-Z0-9]+>','',text).strip()
    if not clean: return
    logger.info('Received request in channel %s at %s',channel,ts)
    name=username(uid)
    cand=[x for x in retrieve(clean,5) if x['score']>=TH]
    result=generate(clean,name,cand)
    response=result['response']
    if AUTO:
        client.chat_postMessage(channel=channel,text=response,thread_ts=event.get('thread_ts') or ts)
        logger.info('Posted reply in channel %s', channel)
    else:
        print('\nWOULD SEND:',response,'\nFOR:',clean)
    # Every request that was not safely answered becomes a follow-up. Sensitive items always do.
    if (not result.get('used_prior_answer')) or result.get('sensitive'):
        add_followup(channel=channel,thread_ts=event.get('thread_ts') or ts,requester=uid,requester_name=name,question=clean,summary=result.get('followup_summary',clean[:180]))
    # An API failure must not cause the request to be discarded as processed.
    mark(key)

@app.event('app_mention')
def mention(event, logger):
    try: handle(event)
    except Exception as e: logger.exception(e)

@app.event('message')
def dm(event, logger):
    # Event subscription should be message.im. Ignore non-DM message events here.
    if event.get('channel_type')!='im': return
    try: handle(event)
    except Exception as e: logger.exception(e)

def digest():
    rows=open_followups()
    if not rows: return
    lines=['*Follow-up List*','These items still need your attention today:','']
    for i,r in enumerate(rows,1):
        lines.append(f"{i}. *{r['requester_name']}* — {r['summary']}\n   <slack://channel?team=&id={r['channel']}|Open conversation>")
    text='\n'.join(lines)
    cid=os.getenv('DIGEST_CHANNEL_ID','').strip()
    if not cid:
        cid=client.conversations_open(users=KATY)['channel']['id']
    client.chat_postMessage(channel=cid,text=text)

sched=BackgroundScheduler(timezone=ZoneInfo(TZ))
sched.add_job(digest,'cron',hour=int(os.getenv('DIGEST_HOUR','14')),minute=int(os.getenv('DIGEST_MINUTE','30')))
sched.start()

if __name__=='__main__':
    print('Katy Slack Assistant starting. AUTO_SEND=',AUTO)
    SocketModeHandler(app,APP_TOKEN).start()
