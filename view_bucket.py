import boto3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


load_dotenv()
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')

s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

bucket = s3.list_objects(Bucket=BUCKET_NAME)  ## Need to add ListObject permissions to access policies
