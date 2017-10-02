import tempfile
import os
import re
import hashlib
import datetime
import json
import requests
import random

from rq import get_current_job

from osf_scraper_api.utilities.fs_helper import load_dict
from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.osf_helper import get_fb_scraper, paginate_list
from osf_scraper_api.utilities.fs_helper import file_exists
from osf_scraper_api.utilities.fs_helper import save_file
from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.crawler.utils import get_user_from_user_file, fetch_friends_of_user, get_screenshot_output_key_from_post
from osf_scraper_api.utilities.selenium_helper import restart_selenium
from osf_scraper_api.utilities.rq_helper import get_rq_jobs_for_user, enqueue_job


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
    f = tempfile.NamedTemporaryFile(delete=False)
    f.close()
    temp_path = f.name + '.png'
    found_post = fb_scraper.screenshot_post(post=post, output_path=temp_path)
    if found_post:
        image_url = save_file(source_file_path=temp_path, destination=output_path)
        os.unlink(f.name)
        os.unlink(temp_path)
        _log('++ successfuly uploaded to: `{}`'.format(image_url))
        return True
    else:
        _log('++ no post found at link')
        return False


def screenshot_post(post, fb_scraper):
    try:
        screenshot_post_helper(post=post, fb_scraper=fb_scraper)
        # if we succeeded, then set num_initializations back to 0
        fb_scraper.num_initializations = 0
    except Exception as e:
        _log('++ encountered error: {}'.format(str(e)))
        if fb_scraper.num_initializations < 3:
            _log('++ retrying attempt {}'.format(fb_scraper.num_initializations))
            fb_scraper.re_initialize_driver()
            return screenshot_post(post=post, fb_scraper=fb_scraper)
        else:
            restart_selenium()
            fb_scraper.re_initialize_driver()
            _log('++ giving up on `{}`'.format(post['link']))
            raise e


def screenshot_multi_user_job(input_folder, no_skip, fb_username, fb_password, user_files=None, central_user=None, post_process=False):
    if central_user:
            friends = fetch_friends_of_user(central_user)
            user_files = []
            for index, user in enumerate(friends):
                user_file = '{}/{}.json'.format(input_folder, user)
                # if file exists, append it to list to process
                if file_exists(user_file):
                    user_files.append(user_file)
                    if ENV_DICT.get('TEST_SAMPLE_SIZE'):
                        if len(user_files) > 100:
                            _log('++ truncating list of users to be < 100')
                            break
                if not index % 10:
                    _log('++ loading {}/{}'.format(index, len(friends)))
    all_posts = []
    _log('++ enqueuing screenshot jobs for {} users'.format(len(user_files)))
    for index, user_file in enumerate(user_files):
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
            if ENV_DICT.get('TEST_SAMPLE_SIZE'):
                if len(all_posts) > ENV_DICT.get('TEST_SAMPLE_SIZE'):
                    break
        except:
            _log('++ failed to load posts for user: {}'.format(user_file))
        if not index % 10:
            _log('++ loading posts {}/{}'.format(index, len(user_files)))
    if ENV_DICT.get("TEST_SAMPLE_SIZE"):
        page_size = 2
        all_posts = random.sample(all_posts, min(ENV_DICT.get("TEST_SAMPLE_SIZE"), len(all_posts)))
    else:
        page_size = 100
    # now start jobs to screenshot the posts in pages
    pages = paginate_list(mylist=all_posts, page_size=page_size)
    _log('++ enqueing {} posts in {} jobs'.format(len(all_posts), len(pages)))
    for index, page in enumerate(pages):
        _log('++ enqueing page {}'.format(index))
        enqueue_job(screenshot_posts,
                          posts=page,
                          fb_username=fb_username,
                          fb_password=fb_password,
                          timeout=3600,
                          post_process=post_process
                          )


def screenshot_posts(posts, fb_username, fb_password, post_process=False):
    _log('++ starting screenshot_posts job')
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    num_posts = len(posts)
    _log('++ preparing to screenshot {} posts'.format(num_posts))
    for index, post in enumerate(posts):
        try:
            _log('++ saving screenshot of post: `{}` {}/{}'.format(post['link'], index, num_posts))
            screenshot_post(post=post, fb_scraper=fb_scraper)
        except Exception as e:
            _capture_exception(e)
    _log('++ finished screenshotting all posts')
    fb_scraper.quit_driver()

    if post_process:
        _log('++ running post process check for pending jobs of user {}'.format(fb_username))
        # check if there are any other pending scrape_posts jobs for this user
        rq_jobs = get_rq_jobs_for_user(fb_username=fb_username)
        current_job = get_current_job()
        def filter_fun(job):
            if job.func_name == 'osf_scraper_api.crawler.screenshot.screenshot_posts':
                if job.kwargs.get('fb_username') == fb_username:
                    if not current_job or current_job.id != job.id:
                        return True
            # otherwise return False
            return False
        pending = filter(filter_fun, rq_jobs)
        # if no pending job found, then make request to start pdf job
        if len(pending) == 0:
            _log('++ starting post_process job to create a pdf for user: {}'.format(fb_username))
            job_params = {
                'fb_username': fb_username,
                'fb_password': fb_password
            }
            url = '{API_DOMAIN}/api/crawler/pdf/'.format(API_DOMAIN=ENV_DICT['API_DOMAIN'])
            headers = {'content-type': 'application/json'}
            requests.post(url, data=json.dumps(job_params), headers=headers)
            _log('++ curled job to scrape screenshots of {}'.format(fb_username))
        else:
            _log('++ found {} pending jobs, waiting for other jobs to finish'.format(len(pending)))

