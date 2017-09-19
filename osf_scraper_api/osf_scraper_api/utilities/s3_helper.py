import os

import boto3

from osf_scraper_api.settings import ENV_DICT, PROJECT_PATH


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


def s3_key_exists(s3_path):
    """
    returns True if the given s3_path already exists in s3
    :param s3_path: string of key to test existence of
    :return: boolean
    """
    bucket = get_s3_bucket()
    objs = list(bucket.objects.filter(Prefix=s3_path))
    if len(objs) > 0 and objs[0].key == s3_path:
        return True
    else:
        return False


if __name__ == '__main__':

    # Upload a new file
    f_path = os.path.join(PROJECT_PATH, 'data/maxhfowler@gmail.com-1504899764.json')
    s3_upload_file(source_file_path=f_path, destination='test.json')