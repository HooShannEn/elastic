
from langchain_elasticsearch import ElasticsearchStore
from langchain_aws import BedrockEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from dotenv import load_dotenv
import os

load_dotenv()

embeddings = BedrockEmbeddings(
    model_id='amazon.titan-embed-text-v2:0',
    region_name=os.getenv('AWS_REGION')
)
loader = PyPDFDirectoryLoader('docs/')
documents = loader.load()
print(f'Loaded {len(documents)} pages')

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(documents)

# Tag chunks by type for filtered availability queries
for chunk in chunks:
    source = chunk.metadata.get('source', '').lower()
    if any(w in source for w in ['food', 'bank', 'voucher', 'meal']):
        chunk.metadata['category'] = 'food'
    else:
        chunk.metadata['category'] = 'shelter'

store = ElasticsearchStore.from_documents(
    chunks, embeddings,
    es_cloud_id=os.getenv('ELASTIC_CLOUD_ID'),
    es_api_key=os.getenv('ELASTIC_API_KEY'),
    index_name=os.getenv('ELASTIC_INDEX_FOOD')
)
print('Done! Food & shelter index ready.')
