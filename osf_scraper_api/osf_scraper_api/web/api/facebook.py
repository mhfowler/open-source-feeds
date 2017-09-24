import re
import hashlib

from flask import make_response, jsonify, Blueprint, request

from osf_scraper_api.utilities.fb_helper import fetch_friends_of_user
from osf_scraper_api.web.jobs.fb_posts import scrape_fb_posts
from osf_scraper_api.web.jobs.fb_friends import scrape_fb_friends
from osf_scraper_api.web.jobs.screenshot import screenshot_posts
from osf_scraper_api.web.jobs.test_rq import test_rq
from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.fs_helper import file_exists, load_dict, list_files_in_folder
from osf_scraper_api.settings import TEMPLATE_DIR


def screenshot_helper(user_file, input_folder, no_skip, fb_username, fb_password):
    match = re.match('(.*)\.json', user_file)
    if match:
        user = match.group(1)
    else:
        user = user_file
    user = user.replace(input_folder, '')
    if user.startswith('/'):
        user = user[1:]
    user_posts = load_dict(user_file)['posts'][user]
    posts_to_scrape = []
    for post in user_posts:
        post_link = post['link']
        match = re.match('.*/posts/(\d+)', post_link)
        if match:
            post_id = match.group(1)
        else:
            post_id = 'XX' + str(int(hashlib.sha1(post_link).hexdigest(), 16) % (10 ** 8))
        output_key = 'screenshots/{}-{}.png'.format(user, post_id)
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


def get_facebook_blueprint(osf_queue):
    facebook_blueprint = Blueprint('facebook_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @facebook_blueprint.route('/api/test_rq/<test_id>/', methods=['GET'])
    def test_rq_endpoint(test_id):
        osf_queue.enqueue(test_rq, test_id)
        return make_response(jsonify({
            'message': 'Job enqueued for scraping.'
        }), 200)

    @facebook_blueprint.route('/api/fb_friends/', methods=['POST'])
    def fb_friends_endpoint():
        params = request.get_json()
        users = params.get('users')
        if users != 'all_friends':
            _log('++ enqueing fb_friends job')
            osf_queue.enqueue(scrape_fb_friends,
                users=params['users'],
                fb_username=params['fb_username'],
                fb_password=params['fb_password'],
                no_skip=params.get('no_skip')
            )
        else:
            central_user = params.get('central_user')
            friends = fetch_friends_of_user(central_user)
            for friend in friends:
                _log('++ enqueing fb_friends job for: {}'.format(friend))
                osf_queue.enqueue(scrape_fb_friends,
                  users=[friend],
                  fb_username=params['fb_username'],
                  fb_password=params['fb_password'],
                  no_skip=params.get('no_skip')
                )
        return make_response(jsonify({
            'message': 'fb_friend job enqueued'
        }), 200)

    @facebook_blueprint.route('/api/fb_posts/', methods=['POST'])
    def fb_posts_endpoint():
        params = request.get_json()
        job_name = params.get('job_name')
        # if a job_name is provided, then create a separate queue job for each user
        if job_name:
            _log('++ enqueing fb_posts job for each user provided')
            users = params.get('users')
            if users == 'all_friends':
                central_user = params.get('central_user')
                _log('++ looking up users from friends of central_user: {}'.format(central_user))
                users = fetch_friends_of_user(central_user)
            for user in users:
                key_name = 'jobs/{}/{}.json'.format(job_name, user)
                # if already exists then skip
                if params.get('no_skip') is not True:
                    if file_exists(key_name):
                        _log('++ skipping {}'.format(key_name))
                        continue
                # otherwise scrape and then save this user
                params['users'] = [user]
                params['output_path'] = key_name
                params['replace'] = True
                if params.get('job_name'):
                    del params['job_name']
                _log('++ enqueing fb_posts job for user {}'.format(user))
                osf_queue.enqueue(scrape_fb_posts, params)
        else:
            _log('++ enqueing fb_posts job')
            osf_queue.enqueue(scrape_fb_posts, params)
        # finally return 'OK' response
        return make_response(jsonify({
            'message': 'fb_post job enqueued'
        }), 200)

    @facebook_blueprint.route('/api/fb_screenshots/', methods=['POST'])
    def fb_screenshots_endpoint():
        params = request.get_json()
        input_folder = params['input_folder']
        user_files = list_files_in_folder(input_folder)
        no_skip = params.get('no_skip') is not True
        fb_username = params['fb_username']
        fb_password = params['fb_password']
        for user_file in user_files:
            _log('++ screenshotting posts for {}'.format(user_file))
            try:
                screenshot_helper(
                    user_file=user_file,
                    input_folder=input_folder,
                    fb_username=fb_username,
                    fb_password=fb_password,
                    no_skip=no_skip
                )
            except Exception as e:
                _log('++ failed to screenshot user_file: {}'.format(user_file))
                _capture_exception(e)
        return make_response(jsonify({
            'message': 'fb_screenshot job enqueued'
        }), 200)

    return facebook_blueprint
