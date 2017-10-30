"""
This file looks for an env.json file in the root of backend
which determines many configuration properties for the app,
such as which database to connect to, and supplying secrets.

Ansible ensures that prod and staging having a different env.json file to allow them to work differently.

If you would like to locally simulate the environment of staging or prod,
you can set the environmental variable HELLO_FORCE_USE_ENVIRON
This will cause hello_settings.py to look in a different location for env.json (see FORCE_ENVIRON below)

Constants from this file can be freely imported from anywhere in the backend.
This file should import from no other files in the project.
"""
import os
import json

# project path
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
print 'PROJECT_PATH: {}'.format(PROJECT_PATH)

# configure path to env.json (default is env.json but can use FORCE_ENVIRON to override this)
FORCE_ENVIRON = os.environ.get('HELLO_ENV')
if FORCE_ENVIRON == 'prod':
    ENV_PATH = os.path.join(PROJECT_PATH, '../devops/secret_files/env/prod')
elif FORCE_ENVIRON == 'staging':
    ENV_PATH = os.path.join(PROJECT_PATH, '../devops/secret_files/env/staging')
elif FORCE_ENVIRON == 'test':
    ENV_PATH = os.path.join(PROJECT_PATH, '../devops/secret_files/env/test')
else:
    ENV_PATH = os.path.join(PROJECT_PATH, 'env.json')
print 'ENV_PATH: {}'.format(ENV_PATH)

# load env.json into ENV_DICT
ENV_DICT = json.loads(open(ENV_PATH, "r").read())

# load env variables from host
if os.environ.get('HOST_IP_ADDRESS'):
    ENV_DICT['HOST_IP_ADDRESS'] = os.environ.get('HOST_IP_ADDRESS')

# paths
FLASK_DIR = os.path.join(PROJECT_PATH, 'hello_webapp')
TEMPLATE_DIR = os.path.join(PROJECT_PATH, 'templates')
DATA_DIR = os.path.join(PROJECT_PATH, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if ENV_DICT.get('FS_BASE_PATH'):
    if not os.path.exists(ENV_DICT.get('FS_BASE_PATH')):
        os.makedirs(ENV_DICT.get('FS_BASE_PATH'))

# settings
SELENIUM_URL = ENV_DICT.get('SELENIUM_URL')
print 'SELENIUM_URL: {}'.format(SELENIUM_URL)

# constants
NUMBER_OF_POST_SWEEPS = 2
NUMBER_OF_SCREENSHOT_SWEEPS = 2
MIN_TIME_TO_PIPELINE_CHECK = 30

# defaults
DEFAULT_JOB_TIMEOUT = 300
