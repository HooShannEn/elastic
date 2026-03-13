from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime
import os, random, string

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'],
    allow_methods=['*'], allow_headers=['*'])

es = Elasticsearch(
    cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
    api_key=os.getenv('ELASTIC_API_KEY')
)

class CaseCreate(BaseModel):
    profile: dict
    referrals: list = []
    urgency: str = 'none'

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.post('/case/new')
def create_case(data: CaseCreate):
    code = gen_code()
    doc = {
        'code': code,
        'profile': data.profile,
        'referrals': data.referrals,
        'urgency': data.urgency,
        'created_at': datetime.utcnow().isoformat(),
        'last_seen': datetime.utcnow().isoformat()
    }
    es.index(index='bridgeai-cases', id=code, document=doc)
    return {'code': code, 'message': 'Case created'}

@app.get('/case/{code}')
def get_case(code: str):
    try:
        res = es.get(index='bridgeai-cases', id=code)
        case = res['_source']
        days = (datetime.utcnow() - datetime.fromisoformat(case['last_seen'])).days
        summary = f"Last seen {days} days ago. Referrals: {', '.join(case['referrals']) or 'none yet'}."
        # Update last seen
        es.update(index='bridgeai-cases', id=code,
            doc={'last_seen': datetime.utcnow().isoformat()})
        return {'found': True, 'summary': summary, 'case': case}
    except:
        return {'found': False, 'summary': 'Case not found'}

@app.post('/case/{code}/referral')
def add_referral(code: str, referral: dict):
    es.update(index='bridgeai-cases', id=code,
        script={'source': 'ctx._source.referrals.add(params.r)',
                'params': {'r': referral['service']}})
    return {'status': 'updated'}

@app.post('/outcome')
def log_outcome(data: dict):
    # Logs 'did you get help?' responses for Kibana dashboard
    es.index(index='bridgeai-outcomes', document={
        'code': data.get('code'),
        'service': data.get('service'),
        'got_help': data.get('got_help'),
        'timestamp': datetime.utcnow().isoformat()
    })
    return {'status': 'logged'}
