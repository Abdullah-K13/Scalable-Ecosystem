import boto3
import json

# Initialize clients for S3, SNS, and Glue
s3 = boto3.client('s3')
sns = boto3.client('sns')
glue = boto3.client('glue')

# SNS Topic ARN (replace with your actual ARN)
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:761018873761:group-a'
CRAWLER_NAME = 'group-a-crawler'  # Replace with your Glue crawler name

def lambda_handler(event, context):
    try:
        # Extract bucket name and file key from the event
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']

        print(f"New file added: {file_key} in bucket: {bucket_name}")
        
        # Process the file (if needed, e.g., merging or reading data)
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        data = obj['Body'].read().decode('utf-8')

        print(f"File content read successfully from: {file_key}")
        
        # Notify via SNS
        sns_message = f"File '{file_key}' was successfully uploaded to the bucket '{bucket_name}'. Thanks for adding a new file!"
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=sns_message,
            Subject="New File Added to S3"
        )

        print("Notification sent via SNS.")
        
        # Trigger the Glue crawler
        glue.start_crawler(Name=CRAWLER_NAME)
        print(f"Glue crawler '{CRAWLER_NAME}' started successfully.")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Success: File processed, notification sent, and crawler started!')
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
