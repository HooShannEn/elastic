from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_elasticsearch import ElasticsearchStore
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from availability import format_food_response, get_shelters
from handoff import detect_crisis, generate_referral_summary, escalate_to_worker
from dotenv import load_dotenv
import os
from elasticsearch import Elasticsearch

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'],
    allow_methods=['*'], allow_headers=['*'])

es = Elasticsearch(
    cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
    api_key=os.getenv('ELASTIC_API_KEY')
)

def get_rag():
    embeddings = BedrockEmbeddings(
        model_id='amazon.titan-embed-text-v2:0',
        region_name=os.getenv('AWS_REGION')
    )
    store = ElasticsearchStore(
        es_cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
        es_api_key=os.getenv('ELASTIC_API_KEY'),
        index_name=os.getenv('ELASTIC_INDEX_FOOD'),
        embedding=embeddings
    )
    llm = ChatBedrock(
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
        region_name=os.getenv('AWS_REGION')
    )

    prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for people seeking food and shelter assistance in Singapore.
Use the following context to answer the question. If you don't know, say so honestly.

Context:
{context}

Question: {question}

Answer:""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {
            "context": store.as_retriever(search_kwargs={"k": 4}) | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain

@app.post('/food/ask')
def ask_food(data: dict):
    question = data.get('question', '')
    profile = data.get('profile', {})
    case_code = data.get('case_code')

    # Crisis detection first
    if detect_crisis(question):
        summary = generate_referral_summary(question, profile)
        result = escalate_to_worker(summary, case_code)
        return {
            'type': 'crisis_escalation',
            'answer': result['message'],
            'referral_summary': result['summary'],
            'escalated': True
        }

    chain = get_rag()

    # Food question
    if any(w in question.lower() for w in ['food bank', 'food', 'eat', 'hungry', 'meal']):
        availability = format_food_response()
        rag_answer = chain.invoke(question)
        return {
            'type': 'food',
            'answer': rag_answer,
            'availability': availability,
            'escalated': False
        }

    # Shelter question
    if any(w in question.lower() for w in ['shelter', 'sleep', 'housing', 'evict', 'homeless']):
        shelters = get_shelters()
        rag_answer = chain.invoke(question)
        return {
            'type': 'shelter',
            'answer': rag_answer,
            'shelters': shelters,
            'escalated': False
        }

    # General question
    return {'type': 'general', 'answer': chain.invoke(question), 'escalated': False}

@app.get('/food/availability')
def food_availability():
    return {'food_banks': format_food_response(), 'shelters': get_shelters()}