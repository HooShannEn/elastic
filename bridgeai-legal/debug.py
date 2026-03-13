import boto3, os
print("Region:", os.getenv('AWS_REGION'))
print("Key ID:", os.getenv('AWS_ACCESS_KEY_ID', 'NOT SET')[:8] + '...')

# Test bedrock connection
client = boto3.client('bedrock', region_name=os.getenv('AWS_REGION'))
models = client.list_foundation_models()
titan_models = [m['modelId'] for m in models['modelSummaries'] if 'titan-embed' in m['modelId']]
print("Available titan embed models:", titan_models)