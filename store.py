import json, os, sqlite3, time
from pathlib import Path

DATA = Path('data'); DATA.mkdir(exist_ok=True)
DB = DATA / 'assistant.db'

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.execute('''CREATE TABLE IF NOT EXISTS followups(id INTEGER PRIMARY KEY, channel TEXT, thread_ts TEXT, requester TEXT, requester_name TEXT, question TEXT, summary TEXT, created REAL, resolved INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS processed(event_key TEXT PRIMARY KEY, created REAL)''')
    c.commit(); return c

def seen(key):
    c=conn(); r=c.execute('SELECT 1 FROM processed WHERE event_key=?',(key,)).fetchone(); c.close(); return bool(r)

def mark(key):
    c=conn(); c.execute('INSERT OR IGNORE INTO processed VALUES (?,?)',(key,time.time())); c.commit(); c.close()

def add_followup(**kw):
    c=conn(); c.execute('INSERT INTO followups(channel,thread_ts,requester,requester_name,question,summary,created) VALUES(?,?,?,?,?,?,?)',
        (kw['channel'],kw['thread_ts'],kw['requester'],kw['requester_name'],kw['question'],kw['summary'],time.time())); c.commit(); c.close()

def open_followups():
    c=conn(); rows=c.execute('SELECT * FROM followups WHERE resolved=0 ORDER BY created').fetchall(); c.close(); return rows
