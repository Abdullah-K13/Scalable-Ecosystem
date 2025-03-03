import boto3
import json

# Initialize the SNS client
sns = boto3.client('sns')

# Replace with your SNS Topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:123456789012:my-sns-topic'

def lambda_handler(event, context):
    try:
        # Extract bucket name and object key from the S3 event
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']

        # Log the event details
        print(f"New file uploaded: {file_key} in bucket: {bucket_name}")

        # Create the SNS message
        message = f"A new file '{file_key}' has been uploaded to the S3 bucket '{bucket_name}'."

        # Publish the message to the SNS topic
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="S3 File Upload Notification"
        )

        print("Notification sent via SNS successfully.")

        return {
            'statusCode': 200,
            'body': json.dumps('Notification sent successfully!')
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failed to send notification: {str(e)}")
        }
