import json
import os
import boto3

bedrock_agent = boto3.client('bedrock-agent')

def lambda_handler(event, context):
    knowledge_base_id = os.environ['KNOWLEDGE_BASE_ID']
    data_source_id = os.environ['DATA_SOURCE_ID']
    
    try:
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Knowledge Base sync started',
                'ingestionJobId': response['ingestionJob']['ingestionJobId']
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
