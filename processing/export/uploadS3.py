import boto3
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv
load_dotenv()

def upload(file, station, date):

    ACCESS_KEY = os.getenv('ACCESS_KEY')
    SECRET_KEY = os.getenv('SECRET_KEY')
    BUCKET_NAME = os.getenv('BUCKET_NAME')

    year, month, day = str(date.year), str(date.month), str(date.day)

    ## Using this intentionally instead of os.path.join() to keep with S3 format
    bucket_folder_prefix = "{}/{}/{}/{}/".format(year, month, day, station)

    s3 = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )

    if (os.path.isdir(file)):   ## File input is a folder of files
        for filename in os.listdir(file):
            s3.upload_file(os.path.join(file, filename), BUCKET_NAME, bucket_folder_prefix + filename)
    else:                     ## File input is an individual file
        s3.upload_file(os.path.join(file, filename), BUCKET_NAME, bucket_folder_prefix + filename)
