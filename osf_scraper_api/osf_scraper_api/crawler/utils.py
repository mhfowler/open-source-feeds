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


def get_screenshot_output_key_from_post(user, post):
    post_link = post['link']
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
    output_key = 'screenshots/{}-{}-{}.png'.format(user, date_str, post_id)
    return output_key


def save_job_params(fb_username, job_params):
    output_key = 'params/{}.json'.format(fb_username)
    save_dict(data_dict=job_params, destination=output_key)


def load_job_params(fb_username):
    output_key = 'params/{}.json'.format(fb_username)
    job_params = load_dict(output_key)
    return job_params


def save_job_status(status, message=None):
    output_key = 'status.json'
    data_dict = {
        'status': status,
        'message': message
    }
    save_dict(data_dict=data_dict, destination=output_key)


def save_job_stage(user, fb_username, fb_password, stage):
    output_key = 'stage.json'
    data_dict = {
        'user': user,
        'fb_username': fb_username,
        'fb_password': fb_password,
        'stage': stage,
    }
    save_dict(data_dict=data_dict, destination=output_key)


def load_job_stage():
    output_key = 'stage.json'
    if file_exists(output_key):
        return load_dict(path=output_key)
    else:
        return None


def clear_job_stage():
    output_key = 'stage.json'
    if file_exists(output_key):
        save_dict({
            'stage': 'finished'
        }, output_key)


def save_last_uptime(uptime):
    output_key = 'uptime.json'
    save_dict({
        'uptime': uptime
    }, output_key)


def load_last_uptime():
    try:
        if g.last_uptime:
            return g.last_uptime
    except:
        pass
    output_key = 'uptime.json'
    if file_exists(output_key):
        data_dict = load_dict(output_key)
        return data_dict['uptime']
    else:
        now = int(time.time())
        save_last_uptime(now)
        return now


def filter_posts(posts):
    cutoff_date = datetime.datetime(month=11, day=8, year=2016, hour=20)
    def filter_fun(p):
        try:
            d = datetime.datetime.fromtimestamp(int(p['date']))
            if d > cutoff_date:
                return True
            else:
                return False
        except:
            return False

    posts = filter(filter_fun, posts)
    _log('++ filtered down to {} posts after cutoff date'.format(len(posts)))

    # filter more
    def filter_fun(post):
        post_content = post['content']
        text = post_content.get('text')
        if text and ('birthday' in text.lower()):
            return False
        if text and (' bday ' in text.lower()):
            return False
        if text and (' belated ' in text.lower()):
            return False
        if post_content.get('not_just_text'):
            return False
        return True

    posts = filter(filter_fun, posts)
    _log('++ filtered down to {} posts without links'.format(len(posts)))
    return posts