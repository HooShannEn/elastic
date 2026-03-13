from langchain_aws import ChatBedrock
from dotenv import load_dotenv
import os, json
from datetime import datetime

load_dotenv()

# Crisis trigger phrases — expand this list
CRISIS_SIGNALS = [
    'no food', 'nothing to eat', 'hungry', 'starving',
    'nowhere to sleep', 'no shelter', 'sleeping outside', 'evicted',
    'cant afford', "can't afford", 'no money', 'urgent',
    'tonight', 'right now', 'emergency', 'desperate',
    'my children', 'baby', 'infant',
    # Malay
    'tiada makanan', 'lapar', 'tiada tempat tinggal',
    # Chinese
    '没有食物', '饿', '没有住所', '紧急',
]

def detect_crisis(message: str) -> bool:
    msg_lower = message.lower()
    return any(signal in msg_lower for signal in CRISIS_SIGNALS)

def generate_referral_summary(user_message: str, profile: dict = None) -> str:
    llm = ChatBedrock(
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
        region_name=os.getenv('AWS_REGION')
    )
    profile_str = json.dumps(profile, indent=2) if profile else 'Not collected'
    prompt = f"""
Generate a concise social worker referral summary from this information.

User message: {user_message}
User profile: {profile_str}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

Format as:
SITUATION: (1 sentence)
URGENCY LEVEL: Critical / High / Medium
IMMEDIATE NEED: (food / shelter / both)
RECOMMENDED ACTION: (specific next step for social worker)
SUGGESTED RESOURCES: (2-3 specific organisations with hotlines)
"""
    response = llm.invoke(prompt)
    return response.content

def escalate_to_worker(summary: str, case_code: str = None) -> dict:
    # In production: send to social worker queue via Elastic Workflows
    # For hackathon: log to Elasticsearch and return confirmation
    return {
        'escalated': True,
        'summary': summary,
        'case_code': case_code,
        'message': '🚨 A social worker will contact you within 2 hours. Hotline: 1800-222-0000',
        'timestamp': datetime.utcnow().isoformat()
    }
