from langchain_elasticsearch import ElasticsearchStore
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

load_dotenv()

ELIGIBILITY_QUESTIONS = [
    {'key': 'household_size',
     'question': 'How many people live in your household (including yourself)?',
     'zh': '您的家庭有几个人（包括您自己）？'},

    {'key': 'employment',
     'question': 'What is your current employment status?',
     'options': ['Employed', 'Unemployed', 'Self-employed', 'Retired', 'Unable to work'],
     'zh': '您目前的就业状况是什么？'},

    {'key': 'housing',
     'question': 'What type of housing do you live in?',
     'options': ['1-room HDB', '2-room HDB', '3-room HDB', '4-room+ HDB', 'Private', 'No fixed home'],
     'zh': '您住在哪种类型的住所？'},

    {'key': 'age_range',
     'question': 'What is your age group?',
     'options': ['Under 21', '21-55', '56-64', '65 and above'],
     'zh': '您的年龄段是？'},

    {'key': 'urgency',
     'question': 'Do you have an urgent need right now?',
     'options': ['Food assistance', 'Shelter/housing', 'Medical costs', 'Utility bills', 'No urgent need'],
     'zh': '您现在有紧急需要吗？'},
]


def build_eligibility_prompt(profile: dict) -> str:
    return f"""
You are a Singapore social services assistant. Based on this profile, list ALL schemes
this person qualifies for. Be specific — name the exact scheme, eligibility criteria
met, and the exact documents they need to bring.

Profile:
- Household size: {profile.get('household_size')}
- Employment: {profile.get('employment')}
- Housing type: {profile.get('housing')}
- Age group: {profile.get('age_range')}
- Urgent need: {profile.get('urgency')}

List every scheme they qualify for. Format as:
SCHEME NAME | Eligibility met | Documents needed | Where to apply
"""


def get_rag_chain():
    embeddings = BedrockEmbeddings(
        model_id='amazon.titan-embed-text-v2:0',  # this one is fine, keep it
        region_name=os.getenv('AWS_REGION')
    )

    store = ElasticsearchStore(
        es_cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
        es_api_key=os.getenv('ELASTIC_API_KEY'),
        index_name=os.getenv('ELASTIC_INDEX_SOCIAL'),
        embedding=embeddings
    )

    llm = ChatBedrock(
        model_id='us.anthropic.claude-3-5-haiku-20241022-v1:0',  # fast + cheap + active
        region_name=os.getenv('AWS_REGION')
    )

    retriever = store.as_retriever(search_kwargs={'k': 5})

    prompt = ChatPromptTemplate.from_template("""
You are a Singapore social services assistant. Use the retrieved context to answer.

Context:
{context}

Question: {question}
""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def check_eligibility(profile: dict) -> str:
    chain = get_rag_chain()
    query = build_eligibility_prompt(profile)
    return chain.invoke(query)


# --- Example usage ---
if __name__ == "__main__":
    sample_profile = {
        'household_size': 3,
        'employment': 'Unemployed',
        'housing': '2-room HDB',
        'age_range': '21-55',
        'urgency': 'Food assistance',
    }

    result = check_eligibility(sample_profile)
    print(result)