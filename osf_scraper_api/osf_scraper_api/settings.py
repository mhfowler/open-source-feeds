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
FORCE_ENVIRON = os.environ.get('HELLO_FORCE_USE_ENVIRON')
if FORCE_ENVIRON == 'PROD':
    ENV_PATH = os.path.join(PROJECT_PATH, 'devops/secret_files/prod_env.json')
elif FORCE_ENVIRON == 'STAGING':
    ENV_PATH = os.path.join(PROJECT_PATH, 'devops/secret_files/staging_env.json')
elif FORCE_ENVIRON == 'TEST':
    ENV_PATH = os.path.join(PROJECT_PATH, 'devops/secret_files/test_env.json')
else:
    ENV_PATH = os.path.join(PROJECT_PATH, 'env.json')
print 'ENV_PATH: {}'.format(ENV_PATH)

# load env.json into ENV_DICT
ENV_DICT = json.loads(open(ENV_PATH, "r").read())

# paths
FLASK_DIR = os.path.join(PROJECT_PATH, 'hello_webapp')
TEMPLATE_DIR = os.path.join(PROJECT_PATH, 'templates')
DATA_DIR = os.path.join(PROJECT_PATH, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# settings
SELENIUM_URL = ENV_DICT.get('SELENIUM_URL')
print 'SELENIUM_URL: {}'.format(SELENIUM_URL)

DEFAULT_JOB_TIMEOUT = 300
