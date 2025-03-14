from kafka import KafkaConsumer
from time import sleep
import json
from s3fs import S3FileSystem

# Kafka Consumer Setup
consumer = KafkaConsumer(
    'test_topic',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # Deserialize from JSON to Python dict
)

# S3 Configuration
s3 = S3FileSystem()
S3_BUCKET_NAME = "ecosystem-bucket"
S3_FILE_PATH_TEMPLATE = f"s3://{S3_BUCKET_NAME}/group-a/customer_{{}}.csv"

# Consume messages from Kafka and save to S3
for count, message in enumerate(consumer):
    try:
        raw_value = message.value
        if not raw_value:  # Check for empty messages
            print(f"Skipping empty message at count {count}")
            continue

        # Generate a unique file path for each message
        file_path = S3_FILE_PATH_TEMPLATE.format(count)

        # Write the raw CSV line to S3
        with s3.open(file_path, 'w') as file:
            file.write(json.dumps(raw_value))  # Assuming the message is a dictionary

        print(f"File uploaded to S3: {file_path}")
    except Exception as e:
        print(f"Error processing message {count}: {e}")

    sleep(1)  # Optional delay
