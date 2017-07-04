import os, json


# project path
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
print('PROJECT_PATH: {}'.format(PROJECT_PATH))


# secrets dict
SECRETS_PATH = os.path.join(PROJECT_PATH, 'secret.json')
SECRETS_DICT = json.loads(open(SECRETS_PATH, "r").read())


# data
DATA_DIR = os.path.join(PROJECT_PATH, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

friend_dir = os.path.join(DATA_DIR, 'friends')
if not os.path.exists(friend_dir):
    os.makedirs(friend_dir)

posts_dir = os.path.join(DATA_DIR, 'posts')
if not os.path.exists(posts_dir):
    os.makedirs(posts_dir)


def get_posts_file_path(username):
    posts_file = os.path.join(posts_dir, username + '.txt')
    return posts_file


def get_friends_file_path(username):
    friends_file = os.path.join(friend_dir, username + '.txt')
    return friends_file

# are we local?
LOCAL = os.environ.get('LOCAL')
DEBUG = LOCAL


# temporary settings below
