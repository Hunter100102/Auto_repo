import json, math, os, re
from pathlib import Path
from openai import OpenAI

client=OpenAI()
MODEL=os.getenv('OPENAI_MODEL','gpt-5.6-luna')
HISTORY=Path('data/history.jsonl')

def embed(text):
    return client.embeddings.create(model='text-embedding-3-small', input=text[:8000]).data[0].embedding

def cosine(a,b):
    d=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b)); return d/(na*nb) if na and nb else 0

def retrieve(question,k=5):
    if not HISTORY.exists(): return []
    q=embed(question); rows=[]
    for line in HISTORY.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        r=json.loads(line); r['score']=cosine(q,r['embedding']); rows.append(r)
    return sorted(rows,key=lambda x:x['score'],reverse=True)[:k]

def generate(question, requester_name, candidates):
    examples='\n\n'.join([f"Similarity {c['score']:.3f}\nKaty previously wrote: {c['text']}" for c in candidates]) or '(none)'
    prompt=f'''You are a conservative Slack acknowledgment assistant for Katy.
New message from {requester_name}: {question}

Potential prior Katy messages retrieved from Slack:
{examples}

Rules:
- Historical messages are evidence of Katy's writing style and, only when they directly answer the same operational question, may provide an answer.
- Never infer a factual answer merely because wording is similar.
- Never invent status, ETA, schedule, technician location, completion, price, approval, policy, or other facts.
- If a prior message clearly contains a reusable answer to the same question, write a short response grounded ONLY in that answer and set used_prior_answer=true.
- Otherwise write a friendly, human acknowledgment in Katy's style, such as saying she is looking into it and will get back to them by end of day. Do not answer the question.
- Do not promise end-of-day if the incoming message itself indicates an emergency, legal/HR matter, safety issue, financial dispute, or other sensitive/high-stakes issue. In those cases acknowledge only and set sensitive=true.
- Keep it concise and natural; do not mention AI, databases, searches, or automation.
- Return JSON only with keys: response, used_prior_answer, sensitive, followup_summary.
'''
    r=client.responses.create(model=MODEL,input=prompt)
    text=r.output_text.strip()
    text=re.sub(r'^```json\s*|\s*```$','',text,flags=re.S)
    return json.loads(text)
