import json
import boto3
import uuid
import logging
import os
import re
from datetime import datetime


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def apply_guardrail(bedrock_runtime, content, guardrail_id, guardrail_version="DRAFT"):
    """
    Apply Bedrock Guardrail to content for redaction
    
    Args:
        bedrock_runtime: Boto3 client for Bedrock Runtime
        content: The text content to apply guardrails to
        guardrail_id: The ID of the guardrail to apply
        guardrail_version: Version of the guardrail to use
        
    Returns:
        The redacted/filtered content
    """
    try:
        # Format content according to the API requirements
        formatted_content = [
            {
                "text": {
                    "text": content
                }
            }
        ]
        
        # Call the guardrail API
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source="OUTPUT",  # Using OUTPUT as the source based on testing
            content=formatted_content
        )
        
        # Check if guardrail intervened and we got outputs
        if 'action' in response and response['action'] == 'GUARDRAIL_INTERVENED' and 'outputs' in response and response['outputs']:
            logger.info(f"Guardrail successfully intervened. Analyzing outputs...")
            
            # Try different response formats
            if len(response['outputs']) > 0:
                output = response['outputs'][0]
                
                # Try standard format
                if 'text' in output and isinstance(output['text'], dict) and 'text' in output['text']:
                    return output['text']['text']
                    
                # Try alternative format where text might be directly in output
                elif 'text' in output and isinstance(output['text'], str):
                    return output['text']
                    
                # Try another alternative where content might be at a different path
                elif 'content' in output:
                    if isinstance(output['content'], str):
                        return output['content']
                    elif isinstance(output['content'], dict) and 'text' in output['content']:
                        return output['content']['text']
                
                # Log the output structure for debugging
                logger.warning(f"Could not extract text from response output: {json.dumps(output)}")
        
        # If no redacted output, log details and return original content
        logger.warning(f"No redacted output from guardrail. Action: {response.get('action')}")
        if 'usage' in response:
            logger.info(f"Guardrail usage stats: {json.dumps(response['usage'])}")
        return content
    except Exception as e:
        logger.error(f"Error applying guardrail: {str(e)}")
        # Return original content if guardrail application fails
        return content

def lambda_handler(event, context):
    # Create Boto3 clients
    s3 = boto3.client('s3')
    bedrock = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
    # Use bedrock-runtime for guardrails, not bedrock-agent-runtime
    bedrock_runtime = bedrock  # reuse the same client for both model invocation and guardrails
    
    # Guardrail ID - using the ARN from environment variable (required)
    # guardrail_id = os.environ['GUARDRAIL_ID']
    # if not guardrail_id:
    #     raise ValueError("GUARDRAIL_ID environment variable must be set")
    
    # Extract bucket name and object key from the speaker identification output
    # speaker_identification = event.get('SpeakerIdentification', {})
    # speaker_payload = speaker_identification.get('Payload', {})
    # bucket_name = speaker_identification.get('bucket_name')
    # object_key = speaker_identification.get('object_key')

    bucket_name = event.get('bucket_name')
    object_key = event.get('object_key')

    print(bucket_name)
    print(object_key)

    
    if not bucket_name or not object_key:
        print("Missing bucket_name or object_key in input")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing bucket_name or object_key in input'})
        }
    
    # Download the object from S3
    file_obj = s3.get_object(Bucket=bucket_name, Key=object_key)
    content = file_obj['Body'].read().decode('utf-8')
    
    # Apply guardrail to redact sensitive content in the transcription
    logger.info("Applying guardrail to transcription...")
    # redacted_content = apply_guardrail(bedrock_runtime, content, guardrail_id)
    
    # Log redaction statistics if content was modified
    # if content != redacted_content:
    #     logger.info("Sensitive content was redacted from transcription")

    # Construct the prompt with redacted content
    prompt = f"{content}\n\nGive me the summary, speakers, key discussions, and action items in japanese"

    # Construct the request payload
    body = json.dumps({
        "max_tokens": 4096,
        "temperature": 0.5,
        "messages": [{"role": "user", "content": prompt}],
        "anthropic_version": "bedrock-2023-05-31"
    })
    
    # Invoke the model
    modelId = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    response = bedrock.invoke_model(body=body, modelId=modelId)
    
    # Parse the response
    response_body = json.loads(response.get("body").read())
    content = response_body.get("content")
    summary = content[0]['text']
    
    # Optionally apply guardrail again to the summary to ensure all sensitive content is redacted
    # logger.info("Applying guardrail to generated summary...")
    # redacted_summary = apply_guardrail(bedrock_runtime, summary, guardrail_id)
    
    # Log if any additional content was redacted from the summary
    # if summary != redacted_summary:
    #     logger.info("Additional sensitive content was redacted from summary")
    
    # Generate output filename
    # Input: Transcription-Output-for-uploads/sample-team-meeting-recording-XXXX-XXXX-XXXX-XXXX.mp4-speaker-identification.txt
    # Output: Bedrock-Sonnet-GenAI-summary-sample-team-meeting-recording-XXXX-XXXX-XXXX-XXXX.txt

    # 特定のRAG用のS3データソースに格納
    output_bucket_name = "kendra-s3-datasource"
    object_prefix = "shokken-sales/"
    # 現在日をyyyyMMdd形式で取得
    current_date = datetime.now().strftime('%Y%m%d')
    


    base_name = object_key.split('/')[-1]
    file_id = base_name.replace('Transcription-Output-for-', '').replace('.wav-speaker-identification.txt', '')
    output_key = f"{object_prefix}{current_date}-{file_id}.txt"
    
    # Use the same bucket for summaries
    summaries_bucket = bucket_name
    
    s3.put_object(Bucket=output_bucket_name, Key=output_key, Body=summary.encode('utf-8'))

    # メタデータファイルの作成

    ## メタデータスキーマ定義
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "Simplified schema for analyzing and summarizing meeting minutes",
        "type": "object",
        "properties": {
            "metadataAttributes":{
                "customer": {
                "type": "string",
                "description": "Unique identifier for the customer name.",
                "maxLength": 50
                },
                "customer_category": {
                    "type": "string",
                    "description": "Customer category, for example restaurant, supermarket, hotel and so on. English only",
                    "maxLength": 50
                },
                "sentiment": {
                    "type": "string",
                    "description": "the deal is positive or negative",
                    "maxLength": 10
                },
                "date": {
                    "type": "string",
                    "description": "meeting date, yyyy-MM-dd format",
                    "maxLength": 15
                },
                "title": {
                    "type": "string",
                    "description": "Short title of the meeting.",
                    "maxLength": 20
                },
                "revenue": {
                    "type": "string",
                    "description": "The amount of the contract, proposal, or estimate within the deal. If there is no information about the amount, set it to None",
                },
                "practicality_score": {
                    "type": "string",
                    "description": "The practicality of this deal. The degree to which this negotiation becomes good practice or information for other sales, marketing, and product development. Estimate practicality between 0 and 100 (maximum 100)",
                },
                "keywords": {
                    "type": "string",
                    "description": "The keyword for this deal. Words that have appeared multiple times in business negotiations or words that symbolize business negotiations",
                }
            },
        "required": ["customer_category", "sentiment", "title", "practicality_score", "keywords"]
        }
    }

    ## メタデータ作成指示プロンプト
    # instructions =  f"""
    #     <input>{content}</input>
    #     "You are an AI system tasked with analyzing meeting minutes to extract metadata.\n"
    #     "1. Analyze the meeting minutes data provided within <input> tags. \n"
    #     "2. Return a JSON response that complies with the provided schema. \n"
    #     "3. If required fields are missing, return available fields with 'null' "
    #     "for missing ones, and add an 'error' field explaining why.\n"
    #     "Example of a valid JSON response: \n"
    #     {
    #         "metadataAttributes": {
    #             "customer": "グランドホテル東京",
    #             "customer_category": "hotel",
    #             "sentiment": "positive",
    #             "title": "業務用唐揚げの提案商談",
    #             "revenue": "￥3,180,000",
    #             "practicality_score": "85",
    #             "keywords": "唐揚げ, 朝食バイキング, 定期配送",
    #             "date": "2025-10-15"
    #         }
    #     }
    # """

    instructions = (
        f"<input>{content}</input>\n"
        f"<date>{current_date}</date>\n"
        "You are an AI system tasked with analyzing meeting minutes to extract "
        "data.\n"
        "1. Analyze the meeting minutes data provided within <input> tags and meeting data within <date> tags. \n"
        "2. Return a JSON response that complies with the provided schema. \n"
        "3. If required fields are missing, return available fields with 'null' "
        "for missing ones, and add an 'error' field explaining why.\n"
        "Example of a valid JSON response: \n"
        "{\n"
        " \"metadataAttributes\": \"{\n"
        " \"customer_category\": hotel,\n"
        " \"sentiment\": positive,\n"
        " \"date\": 2025-11-30,\n"
        " \"title\": \"居酒屋への業務用からあげの提案商談\"\n"
        " \"revenue\": \"￥40,000,000\"\n"
        " \"practicality_score\": \"95\"\n"
        " \"keywords\": \"受注, 唐揚げ, 裏メニュー\"\n"
        "}\n"
        "}"
    )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 1,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instructions},
                    {"type": "text", "text": json.dumps(schema)},
                ]
            }
        ]
    }

    response_invoke = bedrock.invoke_model(
        modelId=modelId,
        body=json.dumps(body)
    )

    response_output = json.loads(response_invoke.get('body').read())

    # レスポンスからテキスト部分を取得
    response_text = response_output['content'][0]['text']

    # ```json から ``` までの部分を正規表現で抽出
    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    print(json_match)

    if json_match:
        # JSON部分のみを取得
        json_string = json_match.group(1)
        
        # JSONとして解析
        try:
            result_json = json.loads(json_string)
            print(type(result_json))
            
            # 綺麗に整形して出力
            print(json.dumps(result_json, indent=2, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
    else:
        print("JSON部分が見つかりませんでした")
    
    metadata_output_key = f"{object_prefix}{current_date}-{file_id}.txt.metadata.json"
    
    # Use the same bucket for summaries
    summaries_bucket = bucket_name
    
    s3.put_object(Bucket=output_bucket_name, Key=metadata_output_key, Body=json_string.encode('utf-8'))
    


    return {
        'bucket_name': summaries_bucket,
        'object_key': output_key,
        'message': 'Summary and key discussions generated successfully'
    }
