import boto3
from io import StringIO
import json
import pandas as pd
from datetime import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator

# Function to convert Kelvin to Fahrenheit
def kelvin_to_fahrenheit(temp_in_kelvin):
    temp_in_fahrenheit = (temp_in_kelvin - 273.15) * (9/5) + 32
    return round(temp_in_fahrenheit, 3)

# Function to transform data and save it to S3 using boto3
def transform_and_save_to_s3(task_instance):
    # Extract the weather data from the XCom
    data = task_instance.xcom_pull(task_ids="extract_houston_weather_data")
    
    # Extract required fields and convert them to Fahrenheit
    city = data["name"]
    weather_description = data["weather"][0]['description']
    temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp"])
    feels_like_farenheit = kelvin_to_fahrenheit(data["main"]["feels_like"])
    min_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_min"])
    max_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_max"])
    pressure = data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
    sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
    sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

    # Prepare the transformed data
    transformed_data = {
        "city": city,
        "description": weather_description,
        "temperature_farenheit": temp_farenheit,
        "feels_like_farenheit": feels_like_farenheit,
        "minimun_temp_farenheit": min_temp_farenheit,
        "maximum_temp_farenheit": max_temp_farenheit,
        "pressure": pressure,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "time_of_record": time_of_record,
        "sunrise_local_time": sunrise_time,
        "sunset_local_time": sunset_time
    }
    
    # Save to a pandas DataFrame
    df = pd.DataFrame([transformed_data])
    
    # Get current timestamp for file naming
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d%H%M%S")
    file_name = f"houston_weather_{dt_string}.csv"
    
    # Use boto3 to save the file to S3 with hardcoded credentials (not recommended for production)
    s3_client = boto3.client('s3',
                             aws_access_key_id='your-access-key-id',
                             aws_secret_access_key='your-secret-access-key',
                             region_name='your-region')
    
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # Upload the CSV to S3
    s3_client.put_object(
        Bucket='ecosystem-bucket', 
        Key=f'weather_data/{file_name}', 
        Body=csv_buffer.getvalue()
    )
    
    print(f"Data saved to s3://ecosystem-bucket/weather_data/{file_name}")

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 8),
    'email': ['smaadil688@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}

# Define the DAG
with DAG('weather_dag_to_s3',
         default_args=default_args,
         schedule_interval='@daily',
         catchup=False) as dag:

    # Dummy start task
    start_pipeline = DummyOperator(
        task_id='start_pipeline'
    )
    
    # Sensor to check if the weather API is ready
    is_houston_weather_api_ready = HttpSensor(
        task_id='is_houston_weather_api_ready',
        http_conn_id='weathermap_api',
        endpoint='/data/2.5/weather?q=houston&APPID=f24adae23defaac2f1a37587b4350121'
    )
    
    # Extract weather data from the API
    extract_houston_weather_data = SimpleHttpOperator(
        task_id='extract_houston_weather_data',
        http_conn_id='weathermap_api',
        endpoint='/data/2.5/weather?q=houston&APPID=f24adae23defaac2f1a37587b4350121',
        method='GET',
        response_filter=lambda r: json.loads(r.text),
        log_response=True
    )
    
    # Transform and save the data to S3
    transform_and_save_to_s3_task = PythonOperator(
        task_id='transform_and_save_to_s3',
        python_callable=transform_and_save_to_s3
    )
    
    # Dummy end task
    end_pipeline = DummyOperator(
        task_id='end_pipeline'
    )

    # Task dependencies
    start_pipeline >> is_houston_weather_api_ready >> extract_houston_weather_data >> transform_and_save_to_s3_task >> end_pipeline
