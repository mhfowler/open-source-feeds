import tempfile
import os
import re
import hashlib
import datetime
import time

from osf_scraper_api.utilities.fs_helper import load_dict
from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.osf_helper import get_fb_scraper
from osf_scraper_api.settings import ENV_DICT
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


def screenshot_user_job(user_file, input_folder, no_skip, fb_username, fb_password):
    _log('++ starting screenshots job for: {}'.format(user_file))
    user = get_user_from_user_file(user_file=user_file, input_folder=input_folder)
    user_posts = load_dict(user_file)['posts'][user]
    posts_to_scrape = []
    for post in user_posts:
        output_key = get_screenshot_output_key_from_post(user=user, post=post)
        post['screenshot_path'] = output_key
        if no_skip:
            if file_exists(output_key):
                _log('++ skipping {}'.format(output_key))
            else:
                posts_to_scrape.append(post)
        else:
            posts_to_scrape.append(post)
    if len(posts_to_scrape):
        _log('++ preparing to screenshot {} posts'.format(len(posts_to_scrape)))
        screenshot_posts(posts=posts_to_scrape, fb_username=fb_username, fb_password=fb_password)
    else:
        _log('++ skipping {}, no posts to screenshot'.format(user))


def screenshot_post_helper(post, fb_scraper):
    output_path = post['screenshot_path']
    _log('++ saving screenshot of post: `{}`'.format(post['link']))
    f = tempfile.NamedTemporaryFile(delete=False)
    f.close()
    temp_path = f.name + '.png'
    fb_scraper.screenshot_post(post=post, output_path=temp_path)
    image_url = save_file(source_file_path=temp_path, destination=output_path)
    os.unlink(f.name)
    os.unlink(temp_path)
    _log('++ successfuly uploaded to: `{}`'.format(image_url))


def screenshot_post(post, fb_scraper):
    try:
        screenshot_post_helper(post=post, fb_scraper=fb_scraper)
    except Exception as e:
        _log('++ encountered error: {}'.format(str(e)))
        if fb_scraper.num_initializations < 5:
            _log('++ retrying attempt {}'.format(fb_scraper.num_initializations))
            fb_scraper.re_initialize_driver()
            return screenshot_post(post=post, fb_scraper=fb_scraper)
        else:
            # TODO: cant get docker to run command on its host (need to use SSH or HTTP)
            # if ENV_DICT.get('DOCKER_RESTART'):
            #     _log('++ restarting docker chrome container')
            #     os.system('sudo /usr/local/bin/docker-compose -f /srv/docker-compose.yml restart selenium')
            #     time.sleep(5)
            #     _log('++ chrome restarted')
            _log('++ sleeping 90 (waiting for selenium to restart)')
            time.sleep(90)
            _log('++ giving up on `{}`'.format(post['link']))
            raise e


def screenshot_posts(posts, fb_username, fb_password):
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    for post in posts:
        screenshot_post(fb_scraper=fb_scraper, post=post)


def screenshot_multi_user_job(user_files, input_folder, no_skip, fb_username, fb_password):
    all_posts = []
    for user_file in user_files:
        _log('++ loading posts for user: {}'.format(user_file))
        try:
            user = get_user_from_user_file(user_file=user_file, input_folder=input_folder)
            user_posts = load_dict(user_file)['posts'][user]
            posts_to_scrape = []
            for post in user_posts:
                output_key = get_screenshot_output_key_from_post(user=user, post=post)
                post['screenshot_path'] = output_key
                if no_skip:
                    if file_exists(output_key):
                        pass
                    else:
                        posts_to_scrape.append(post)
                else:
                    posts_to_scrape.append(post)
            # add this users posts to the list of all posts
            all_posts.extend(posts_to_scrape)
        except:
            _log('++ failed to load posts for user: {}'.format(user_file))
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    _log('++ preparing to screenshot {} posts'.format(len(all_posts)))
    for post in all_posts:
        try:
            screenshot_post(post=post, fb_scraper=fb_scraper)
        except Exception as e:
            _capture_exception(e)
    _log('++ finished screenshotting all posts')

