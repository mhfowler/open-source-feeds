import json
import tempfile
import os

from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.utilities.s3_helper import s3_upload_file, s3_get_file_as_string, s3_key_exists, s3_list_files_in_folder


def save_dict(data_dict, destination):
    _, f_path = tempfile.mkstemp()
    try:
        # write contents to file
        contents = json.dumps(data_dict)
        with open(f_path, 'w') as f:
            f.write(contents)
        # save file
        save_file(source_file_path=f_path, destination=destination)
    finally:
        os.unlink(f_path)


def load_dict(path):
    content = get_file_as_string(path=path)
    data_dict = json.loads(content)
    return data_dict


def get_file_as_string(path):
    if ENV_DICT['FS_BIN_TYPE'] == 'S3':
        return s3_get_file_as_string(s3_path=path)
    else:
        raise Exception('++ invalid FS_BIN_TYPE: {}'.format(ENV_DICT['FS_BIN_TYPE']))


def save_file(source_file_path, destination):
    if ENV_DICT['FS_BIN_TYPE'] == 'S3':
        return s3_upload_file(source_file_path=source_file_path, destination=destination)
    else:
        raise Exception('++ invalid FS_BIN_TYPE: {}'.format(ENV_DICT['FS_BIN_TYPE']))


def file_exists(f_path):
    if ENV_DICT['FS_BIN_TYPE'] == 'S3':
        return s3_key_exists(s3_path=f_path)
    else:
        raise Exception('++ invalid FS_BIN_TYPE: {}'.format(ENV_DICT['FS_BIN_TYPE']))


def list_files_in_folder(f_path):
    if ENV_DICT['FS_BIN_TYPE'] == 'S3':
        return s3_list_files_in_folder(s3_path=f_path)
    else:
        raise Exception('++ invalid FS_BIN_TYPE: {}'.format(ENV_DICT['FS_BIN_TYPE']))


if __name__ == '__main__':
    test_dict = {
        'val': 1,
        'name': 'test'
    }
    save_dict(data_dict=test_dict, destination='test2.json')