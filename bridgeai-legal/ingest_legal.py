from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain_aws import BedrockEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os

load_dotenv()

embeddings = BedrockEmbeddings(
    model_id='amazon.titan-embed-text-v2:0',
    region_name=os.getenv('AWS_REGION')
)

# Load each PDF individually, skipping bad files
docs_dir = 'docs/'
documents = []
for filename in os.listdir(docs_dir):
    if filename.endswith('.pdf'):
        filepath = os.path.join(docs_dir, filename)
        try:
            loader = PyPDFLoader(filepath)
            documents.extend(loader.load())
            print(f'✓ Loaded: {filename}')
        except Exception as e:
            print(f'✗ Skipped {filename}: {e}')

print(f'Loaded {len(documents)} pages total')

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(documents)

for chunk in chunks:
    chunk.metadata['domain'] = 'legal_gov'

store = ElasticsearchStore.from_documents(
    chunks, embeddings,
    es_cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
    es_api_key=os.getenv('ELASTIC_API_KEY'),
    index_name=os.getenv('ELASTIC_INDEX_LEGAL')
)
print('Done! Legal index ready.')