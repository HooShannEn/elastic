from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain_aws import BedrockEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to Elastic
embeddings = BedrockEmbeddings(
    model_id='amazon.titan-embed-text-v2:0',
    region_name=os.getenv('AWS_REGION')
)

# Load all PDFs from docs/ folder
loader = PyPDFDirectoryLoader('social service/')
documents = loader.load()
print(f'Loaded {len(documents)} pages from PDFs')

# Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)
chunks = splitter.split_documents(documents)
print(f'Created {len(chunks)} chunks')

# Push to Elasticsearch
store = ElasticsearchStore.from_documents(
    chunks,
    embeddings,
    es_cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
    es_api_key=os.getenv('ELASTIC_API_KEY'),
    index_name=os.getenv('ELASTIC_INDEX_SOCIAL')
)
print('Done! Social services index ready.')
