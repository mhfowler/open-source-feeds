import tempfile
import os
import re
import hashlib
import datetime

from osf_scraper_api.utilities.fs_helper import load_dict
from osf_scraper_api.utilities.log_helper import _log, _log_image
from osf_scraper_api.utilities.osf_helper import get_fb_scraper
from osf_scraper_api.settings import SELENIUM_URL
from osf_scraper_api.utilities.fs_helper import save_dict, file_exists
from osf_scraper_api.utilities.fs_helper import save_file


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


def screenshot_job(user_file, input_folder, no_skip, fb_username, fb_password):
    _log('++ starting screenshots job for: {}'.format(user_file))
    user = get_user_from_user_file(user_file=user_file, input_folder=input_folder)
    user_posts = load_dict(user_file)['posts'][user]
    posts_to_scrape = []
    for post in user_posts:
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
            date_str = ''
        output_key = 'screenshots/{}-{}-{}.png'.format(user, post_id, date_str)
        if no_skip:
            if file_exists(output_key):
                _log('++ skipping {}'.format(output_key))
                continue
        # if not skipped, then add it to the list of posts to screenshot
        post['screenshot_path'] = output_key
        posts_to_scrape.append(post)
    if len(posts_to_scrape):
        _log('++ preparing to screenshot {} posts'.format(len(posts_to_scrape)))
        screenshot_posts(posts=posts_to_scrape, fb_username=fb_username, fb_password=fb_password)
    else:
        _log('++ skipping {}, no posts to screenshot'.format(user))


def screenshot_posts(posts, fb_username, fb_password):

    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    for post in posts:
        output_path = post['screenshot_path']
        _log('++ saving screenshot of post: {}'.format(post['link']))
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        temp_path = f.name + '.png'
        fb_scraper.screenshot_post(post=post, output_path=temp_path)
        image_url = save_file(source_file_path=temp_path, destination=output_path)
        os.unlink(f.name)
        os.unlink(temp_path)
        _log('++ successfuly uploaded to: {}'.format(image_url))
