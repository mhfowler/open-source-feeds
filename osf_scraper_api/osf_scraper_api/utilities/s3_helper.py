import os
import tempfile
import subprocess

import boto3
from boto.s3.connection import S3Connection

from osf_scraper_api.settings import ENV_DICT, PROJECT_PATH


def get_s3_base_url():
    return 'https://s3.amazonaws.com/{}'.format(ENV_DICT['S3_BUCKET_NAME'])


def get_s3_link(s3_path):
    return '{}/{}'.format(get_s3_base_url(), s3_path)


def get_s3_session():
    session = boto3.Session(
        aws_access_key_id=ENV_DICT['AWS_ACCESS_KEY'],
        aws_secret_access_key=ENV_DICT['AWS_SECRET_KEY'],
    )
    s3 = session.resource('s3')
    return s3


def get_s3_bucket():
    s3 = get_s3_session()
    bucket = s3.Bucket(ENV_DICT['S3_BUCKET_NAME'])
    return bucket


def s3_upload_file(source_file_path, destination):
    cmd = 'AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY} AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY} ' \
            'aws s3 cp "{local_path}" "s3://{bucket_name}/{output_path}"'.format(
        AWS_ACCESS_KEY=ENV_DICT['AWS_ACCESS_KEY'],
        AWS_SECRET_ACCESS_KEY=ENV_DICT['AWS_SECRET_KEY'],
        local_path=source_file_path,
        output_path=destination,
        bucket_name=ENV_DICT['S3_BUCKET_NAME']
    )
    os.system(cmd)


def s3_download_file(s3_path, local_path):
    cmd = 'AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY} AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY} ' \
          'aws s3 cp "s3://{bucket_name}/{s3_path}" "{local_path}"'.format(
        AWS_ACCESS_KEY=ENV_DICT['AWS_ACCESS_KEY'],
        AWS_SECRET_ACCESS_KEY=ENV_DICT['AWS_SECRET_KEY'],
        s3_path=s3_path,
        local_path=local_path,
        bucket_name=ENV_DICT['S3_BUCKET_NAME']
    )
    os.system(cmd)


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
    try:
        cmd = 'AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY} AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY} ' \
              'aws s3 ls "s3://{bucket_name}/{s3_path}"'.format(
            AWS_ACCESS_KEY=ENV_DICT['AWS_ACCESS_KEY'],
            AWS_SECRET_ACCESS_KEY=ENV_DICT['AWS_SECRET_KEY'],
            s3_path=s3_path,
            bucket_name=ENV_DICT['S3_BUCKET_NAME']
        )
        output = subprocess.check_output(cmd, shell=True)
        if output:
            return True
        else:
            return False
    except:
        return False


def s3_folders_in_folder_helper(client, bucket_name, prefix=''):
    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        for prefix in result.get('CommonPrefixes', []):
            yield prefix.get('Prefix')


def s3_list_files_in_folder(s3_path):
    conn = S3Connection(ENV_DICT['AWS_ACCESS_KEY'], ENV_DICT['AWS_SECRET_KEY'])
    bucket = conn.get_bucket(ENV_DICT['S3_BUCKET_NAME'])
    keys = bucket.list(prefix=s3_path)
    keys = [k.name for k in keys]
    return keys


def s3_delete_file(s3_path):
    s3 = get_s3_session()
    s3.meta.client.delete_object(Bucket=ENV_DICT['S3_BUCKET_NAME'], Key=s3_path)


if __name__ == '__main__':

    # Upload a new file
    # f_path = os.path.join(PROJECT_PATH, '/Users/maxfowler/Desktop/test.txt')
    # s3_upload_file(source_file_path=f_path, destination='test.json')
    test = s3_key_exists('test.json')
    print test