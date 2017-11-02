import os
import json
import datetime

BASE_PATH = '/Users/maxfowler/Desktop/pw-posts'


def load_posts():
    POSTS_PATH = os.path.join(BASE_PATH, '2017-posts')
    f_names = os.listdir(POSTS_PATH)
    all_posts = []
    for f_name in f_names:
        f_path = os.path.join(POSTS_PATH, f_name)
        posts = json.loads(open(f_path, 'r').read())
        all_posts += posts
    return all_posts


def exp1():
    MONTHS_PATH = os.path.join(BASE_PATH, 'posts-by-month')
    if not os.path.exists(MONTHS_PATH):
        os.makedirs(MONTHS_PATH)
    posts = load_posts()
    posts_by_month = {}
    for post in posts:
        dt = datetime.datetime.fromtimestamp(post['date'])
        month_posts = posts_by_month.setdefault(dt.strftime('%B'), [])
        month_posts.append(post)
    for month, month_posts in posts_by_month.items():
        month_path = os.path.join(MONTHS_PATH, '{}.json').format(month)
        print '++ writing to {}'.format(month_path)
        with open(month_path, 'w') as f:
            f.write(json.dumps(month_posts))


def by_day():
    DAYS_PATH = os.path.join(BASE_PATH, 'posts-by-day')
    if not os.path.exists(DAYS_PATH):
        os.makedirs(DAYS_PATH)
    posts = load_posts()
    posts_by_day = {}
    for post in posts:
        dt = datetime.datetime.fromtimestamp(post['date'])
        day_posts = posts_by_day.setdefault(dt.strftime('%B-%d'), [])
        day_posts.append(post)
    for day, day_posts in posts_by_day.items():
        day_path = os.path.join(DAYS_PATH, '{}.json').format(day)
        print '++ writing to {}'.format(day_path)
        with open(day_path, 'w') as f:
            f.write(json.dumps(day_posts))

def by_week():
    DAYS_PATH = os.path.join(BASE_PATH, 'posts-by-day')
    if not os.path.exists(DAYS_PATH):
        os.makedirs(DAYS_PATH)
    posts = load_posts()
    posts_by_day = {}
    for post in posts:
        dt = datetime.datetime.fromtimestamp(post['date'])
        day_posts = posts_by_day.setdefault(dt.strftime('%B-%d'), [])
        day_posts.append(post)
    for day, day_posts in posts_by_day.items():
        day_path = os.path.join(DAYS_PATH, '{}.json').format(day)
        print '++ writing to {}'.format(day_path)
        with open(day_path, 'w') as f:
            f.write(json.dumps(day_posts))


if __name__ == '__main__':
    by_day()