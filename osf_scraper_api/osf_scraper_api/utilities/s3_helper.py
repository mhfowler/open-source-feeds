import os
import tempfile

import boto3

from osf_scraper_api.settings import ENV_DICT, PROJECT_PATH


def get_s3_base_url():
    return 'https://s3.amazonaws.com/{}'.format(ENV_DICT['S3_BUCKET_NAME'])


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
    return '{}/{}'.format(get_s3_base_url(), destination)


def s3_get_file_as_string(s3_path):
    bucket = get_s3_bucket()
    f, f_path = tempfile.mkstemp()
    bucket.download_file(Key=s3_path, Filename=f_path)
    with open(f_path, 'r') as f:
        content = f.read()
    os.unlink(f_path)
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


def s3_folders_in_folder_helper(client, bucket_name, prefix=''):
    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        for prefix in result.get('CommonPrefixes', []):
            yield prefix.get('Prefix')


def s3_list_files_in_folder(s3_path):
    session = boto3.Session(
        aws_access_key_id=ENV_DICT['AWS_ACCESS_KEY'],
        aws_secret_access_key=ENV_DICT['AWS_SECRET_KEY'],
    )
    client = session.client('s3')
    bucket_name = ENV_DICT['S3_BUCKET_NAME']
    keys = client.list_objects(Bucket=bucket_name, Prefix=s3_path)
    if keys.get('Contents'):
        keys = keys['Contents']
        to_return = [k['Key'] for k in keys]
    else:
        to_return = []
    return to_return


if __name__ == '__main__':

    # Upload a new file
    f_path = os.path.join(PROJECT_PATH, 'data/maxhfowler@gmail.com-1504899764.json')
    s3_upload_file(source_file_path=f_path, destination='test.json')