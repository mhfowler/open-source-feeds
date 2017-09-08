import json
import tempfile

from osf_dashboard.settings import ENV_DICT
from osf_dashboard.utilities.s3_helper import s3_upload_file, s3_get_file_as_string


def save_dict(data_dict, destination):
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write(json.dumps(data_dict))
        save_file(f_path=f.name, destination=destination)


def load_dict(path):
    content = get_file_as_string(path=path)
    data_dict = json.loads(content)
    return data_dict


def get_file_as_string(path):
    if ENV_DICT['FS_BIN_TYPE'] == 'S3':
        s3_get_file_as_string(s3_path=path)
    else:
        raise Exception('++ invalid FS_BIN_TYPE: {}'.format(ENV_DICT['FS_BIN_TYPE']))


def save_file(f_path, destination):
    if ENV_DICT['FS_BIN_TYPE'] == 'S3':
        s3_upload_file(source_file_path=f_path, destination=destination)
    else:
        raise Exception('++ invalid FS_BIN_TYPE: {}'.format(ENV_DICT['FS_BIN_TYPE']))


if __name__ == '__main__':
    test_dict = {
        'val': 1,
        'name': 'test'
    }
    save_dict(data_dict=test_dict, destination='test2.json')