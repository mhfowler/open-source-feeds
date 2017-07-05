import requests
import os
import json
from hello_settings import SECRETS_DICT, DATA_DIR

facebook_base = 'https://graph.facebook.com'
fb_token = SECRETS_DICT['FB_TOKEN']


def fetch_my_id():
    print '++ fetching facebook id'
    url = '{base}/me?access_token={token}'.format(base=facebook_base, token=fb_token)
    r = requests.get(url)
    fb_id = r.json()['id']
    return fb_id


def make_user_dir(fb_id):
    print '++ creating directory for {fb_id}'.format(fb_id=fb_id)
    user_dir = os.path.join(DATA_DIR, fb_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir


def fetch_friends(fb_id):
    print '++ fetching friends of {}'.format(fb_id)
    url = '{base}/{userid}/friends?access_token={token}'.format(base=facebook_base, userid=fb_id, token=fb_token)
    r = requests.get(url)
    friends_dict = r.json()
    total_friends = friends_dict['summary']['total_count']
    print friends_dict
    return friends_dict


def fetch_posts(fb_id):
    print '++ fetching posts of {}'.format(fb_id)
    url = '{base}/{userid}/feed?access_token={token}'.format(base=facebook_base, userid=fb_id, token=fb_token)
    r = requests.get(url)
    posts_dict = r.json()
    print posts_dict



def fetch_feed(fb_id):
    print '++ fetching posts of {}'.format(fb_id)
    url = '{base}/{userid}/home?access_token={token}'.format(base=facebook_base, userid=fb_id, token=fb_token)
    r = requests.get(url)
    feed_dict = r.json()
    print feed_dict


def process_user():
    fb_id = fetch_my_id()
    user_dir = make_user_dir(fb_id)
    friends = fetch_friends(fb_id=fb_id)
    # write friends to file
    friends_file = os.path.join(user_dir, 'friends.txt')
    with open(friends_file, 'w') as f:
        for friend in friends:
            f.write(friend)
    # fetch posts of friends
    posts_dir = os.path.join(DATA_DIR, 'posts')
    if not os.path.exists(DATA_DIR):
        os.makedirs(posts_dir)
    for friend in friends:
        posts = fetch_posts(friend['id'])
        f_path = os.path.join(posts_dir, friend['id'])
        with open(f_path, 'w') as f:
            for post in posts:
                f.write(post)


if __name__ == '__main__':
    # fetch_posts(fb_id='DadNextDoor')
    # process_user()
    # fetch_posts(fb_id='10154619347243162')
    fetch_feed(fb_id='10154619347243162')



