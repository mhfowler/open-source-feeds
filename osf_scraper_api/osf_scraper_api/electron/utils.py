import re
import json
import random
import time
import hashlib
import datetime

from flask import g

from osf_scraper_api.utilities.fs_helper import get_file_as_string
from osf_scraper_api.utilities.fs_helper import file_exists, list_files_in_folder, save_dict, load_dict
from  osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.settings import ENV_DICT


def get_posts_folder():
    return ENV_DICT['POSTS_FOLDER']


def get_user_from_user_file(user_file, input_folder):
    match = re.match('(.*)\.json', user_file)
    if match:
        user = match.group(1)
    else:
        user = user_file
    user = user.replace(input_folder, '')
    if user.startswith('/'):
        user = user[1:]
    return user


def get_user_posts_file(user):
    posts_folder = get_posts_folder()
    key_name = '{}/{}.json'.format(posts_folder, user)
    return key_name


def get_unprocessed_friends(user):

    posts_folder = get_posts_folder()
    user_files = list_files_in_folder(posts_folder)
    users = []
    for user_file in user_files:
        username = get_user_from_user_file(user_file=user_file, input_folder=posts_folder)
        users.append(username)

    friends = fetch_friends_of_user(user)

    unprocessed = []
    for friend in friends:
        if friend not in users:
            unprocessed.append(friend)

    return unprocessed


def fetch_friends_of_user(user):
    key_name = 'friends/{}.json'.format(user)
    # if this user's friends have not been fetched, then first scrape those friends
    if not file_exists(key_name):
        raise Exception('++ must scrape friends before scraping friends of friends')
    friends_data = get_file_as_string(key_name)
    friends_dict = json.loads(friends_data)
    friends = friends_dict[user]
    return friends


def get_screenshot_output_key_from_post(post):
    post_link = post['link']
    page = post['page']
    match = re.match('.*/posts/(\d+)', post_link)
    if match:
        post_id = match.group(1)
    else:
        post_id = 'XX' + str(int(hashlib.sha1(post_link).hexdigest(), 16) % (10 ** 8))
    try:
        d = datetime.datetime.fromtimestamp(int(post['date']))
        date_str = d.strftime('%b%d')
    except:
        date_str = 'None'
    output_key = 'screenshots/{}-{}-{}.png'.format(page, date_str, post_id)
    return output_key


def get_current_friends():
    key_name = 'friends/current.json'
    if not file_exists(key_name):
        return []
    friends_dict = load_dict(key_name)
    friends = []
    for k, v in friends_dict.items():
        friends = friends + v
    friends.sort()
    return friends


def save_current_pipeline(pipeline_name, pipeline_status, pipeline_params={}, pipeline_message=None):
    output_key = 'pipeline.json'
    data_dict = {
        'pipeline_name': pipeline_name,
        'pipeline_status': pipeline_status,
        'pipeline_message': pipeline_message,
        'pipeline_params': pipeline_params,
    }
    save_dict(data_dict=data_dict, destination=output_key)


def clear_pipeline():
    output_key = 'pipeline.json'
    data_dict = {}
    save_dict(data_dict=data_dict, destination=output_key)


def load_current_pipeline():
    output_key = 'pipeline.json'
    if file_exists(output_key):
        return load_dict(output_key)
    else:
        return {}