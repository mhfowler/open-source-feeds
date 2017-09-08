import os

import boto3

from osf_dashboard.settings import ENV_DICT, PROJECT_PATH


def get_s3_bucket():
    session = boto3.Session(
        aws_access_key_id=ENV_DICT['AWS_ACCESS_KEY'],
        aws_secret_access_key=ENV_DICT['AWS_SECRET_KEY'],
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket(ENV_DICT['S3_BUCKET_NAME'])
    return bucket


def s3_upload_file(source_file_path, destination):
    with open(source_file_path, 'r') as f:
        bucket = get_s3_bucket()
        bucket.put_object(Key=destination, Body=f)


def s3_get_file_as_string(s3_path):
    bucket = get_s3_bucket()
    obj = bucket.get_object(Key=s3_path)
    content = obj.Body
    return content


if __name__ == '__main__':

    # Upload a new file
    f_path = os.path.join(PROJECT_PATH, 'data/maxhfowler@gmail.com-1504899764.json')
    s3_upload_file(source_file_path=f_path, destination='test.json')