from flask import make_response, jsonify, Blueprint, request

from osf_scraper_api.crawler.fb_posts import scrape_fb_posts_job
from osf_scraper_api.crawler.screenshot import screenshot_user_job, screenshot_multi_user_job
from osf_scraper_api.crawler.utils import fetch_friends_of_user
from osf_scraper_api.crawler.utils import get_unprocessed_friends
from osf_scraper_api.crawler.utils import get_user_posts_file
from osf_scraper_api.crawler.fb_friends import crawler_scrape_fb_friends
from osf_scraper_api.settings import TEMPLATE_DIR
from osf_scraper_api.utilities.fs_helper import file_exists, list_files_in_folder
from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.osf_helper import paginate_list


def get_crawler_blueprint(osf_queue):
    crawler_blueprint = Blueprint('crawler_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @crawler_blueprint.route('/api/crawler/fb_friends/', methods=['POST'])
    def fb_friends_endpoint():
        params = request.get_json()
        users = params.get('users')
        if users != 'all_friends':
            _log('++ enqueing fb_friends job')
            osf_queue.enqueue(crawler_scrape_fb_friends,
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
                osf_queue.enqueue(crawler_scrape_fb_friends,
                  users=[friend],
                  fb_username=params['fb_username'],
                  fb_password=params['fb_password'],
                  no_skip=params.get('no_skip')
                )
        return make_response(jsonify({
            'message': 'fb_friend job enqueued'
        }), 200)

    @crawler_blueprint.route('/api/crawler/fb_posts/', methods=['POST'])
    def fb_posts_endpoint():
        params = request.get_json()
        users = params.get('users')
        if users == 'all_friends':
            central_user = params.get('central_user')
            _log('++ looking up users from friends of central_user: {}'.format(central_user))
            users = fetch_friends_of_user(central_user)
            users_to_scrape = get_unprocessed_friends(central_user)
        else:
            users_to_scrape = []
            num_skipped = 0
            num_users = len(users)
            for index, user in enumerate(users):
                if not index % 10:
                    _log('++ {}/{}'.format(index, num_users))
                key_name = get_user_posts_file(user)
                # if already exists then skip
                if params.get('no_skip') is not True:
                    if file_exists(key_name):
                        num_skipped +=1
                        continue
                users_to_scrape.append(user)
            _log('++ skipped {} users'.format(num_skipped))

        # now paginate and process
        num_to_scrape = len(users_to_scrape)
        num_total = len(users)
        _log('++ preparing to scrape {} users ({} total)'.format(num_to_scrape, num_total))
        pages = paginate_list(mylist=users_to_scrape, page_size=100)
        _log('++ enqueing {} users in {} jobs'.format(len(users_to_scrape), len(pages)))
        for index, page in enumerate(pages):
            _log('++ enqueing {} job'.format(index))
            osf_queue.enqueue(scrape_fb_posts_job,
                users=page,
                params=params,
                fb_username=params['fb_username'],
                fb_password=params['fb_password'],
                timeout=5000
            )
        # finally return 'OK' response
        return make_response(jsonify({
            'message': 'fb_post job enqueued'
        }), 200)

    @crawler_blueprint.route('/api/crawler/fb_screenshots/', methods=['POST'])
    def fb_screenshots_endpoint():
        params = request.get_json()
        input_folder = params['input_folder']
        user_files = list_files_in_folder(input_folder)
        no_skip = params.get('no_skip') is not True
        fb_username = params['fb_username']
        fb_password = params['fb_password']
        _log('++ enqueuing screenshot jobs for {} users'.format(len(user_files)))
        job_per_user = params.get('job_per_user')
        # if job_per_user, then make one job for each user
        if job_per_user:
            for user_file in user_files:
                osf_queue.enqueue(screenshot_user_job,
                                  user_file=user_file,
                                  input_folder=input_folder,
                                  fb_username=fb_username,
                                  fb_password=fb_password,
                                  no_skip=no_skip,
                                  timeout=600
                                  )
            _log('++ enqueued screenshot jobs for all {} users'.format(len(user_files)))
        # otherwise make a single job for all the posts
        else:
            screenshot_multi_user_job(
              user_files=user_files,
              input_folder=input_folder,
              fb_username=fb_username,
              fb_password=fb_password,
              no_skip=no_skip,
              osf_queue=osf_queue
            )
        return make_response(jsonify({
            'message': 'fb_screenshot job enqueued'
        }), 200)

    return crawler_blueprint
