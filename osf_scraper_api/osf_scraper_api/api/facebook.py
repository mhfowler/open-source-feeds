from flask import make_response, jsonify, Blueprint, request, abort

from osf_scraper_api.jobs.test_rq import test_rq
from osf_scraper_api.utilities.osf_helper import paginate_list
from osf_scraper_api.settings import TEMPLATE_DIR
from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.jobs.run_job import run_job


def get_facebook_blueprint(osf_queue):
    facebook_blueprint = Blueprint('facebook_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @facebook_blueprint.route('/api/fb_friends/', methods=['POST'])
    def fb_friends_endpoint():

        # get params from post
        params = request.get_json()
        users = params.get('users')
        output_bin = params.get('output_bin')
        page_size = params.get('page_size')

        # check for required fields
        required_fields = [
            'users',
            'output_bin',
            'fb_username',
            'fb_password'
        ]
        for req_field in required_fields:
            if req_field not in params.keys():
                abort(make_response(jsonify({'message': '{} field is required.'.format(req_field)}), 422))

        # default page_size is 20
        if not page_size:
            page_size = 20

        # paginate the users by the page size
        _log('++ preparing to scrape friends of {} users'.format(len(users)))
        pages = paginate_list(mylist=users, page_size=page_size)

        # and queue a job for each page
        _log('++ enqueing users in {} jobs'.format(len(pages)))
        for index, page in enumerate(pages):

            # log this job
            _log('++ enqueing {} job'.format(index))
            job_params = {}
            job_params['users'] = page

            # other params
            param_names = [
                'fb_username',
                'fb_password'
            ]
            for param in param_names:
                job_params[param] = params[param]

            # enqueu the job
            osf_queue.enqueue(run_job,
                job_type='scrape_fb_friends',
                job_params=job_params,
                output_bin=output_bin,
                timeout=5000
            )

        # return 200
        return make_response(jsonify({
            'message': 'fb_friends jobs enqueued'
        }), 200)

    @facebook_blueprint.route('/api/fb_posts/', methods=['POST'])
    def fb_posts_endpoint():

        # get params from post
        params = request.get_json()
        users = params.get('users')
        output_bin = params.get('output_bin')
        page_size = params.get('page_size')

        # check for required fields
        required_fields = [
            'users',
            'output_bin',
            'fb_username',
            'fb_password'
        ]
        for req_field in required_fields:
            if req_field not in params.keys():
                abort(make_response(jsonify({'message': '{} field is required.'.format(req_field)}), 422))

        # default page_size is 20
        if not page_size:
            page_size = 20

        # paginate the users by the page size
        _log('++ preparing to scrape posts of {} users'.format(len(users)))
        pages = paginate_list(mylist=users, page_size=page_size)

        # and queue a job for each page
        _log('++ enqueing users in {} jobs'.format(len(pages)))
        for index, page in enumerate(pages):

            # log this job
            _log('++ enqueing {} job'.format(index))
            job_params = {}
            job_params['users'] = page

            # other params
            param_names = [
                'fb_username',
                'fb_password',
                'max_num_posts_per_user',
                'after_timestamp',
                'before_timestamp',
                'jump_to_timestamp'
            ]
            for param in param_names:
                job_params[param] = params.get(param)

            # enqueu the job
            osf_queue.enqueue(run_job,
                job_type='scrape_fb_posts',
                job_params=job_params,
                output_bin=output_bin,
                timeout=5000
            )

        # return 200
        return make_response(jsonify({
            'message': 'fb_friends jobs enqueued'
        }), 200)

    @facebook_blueprint.route('/api/test_rq/<test_id>/', methods=['GET'])
    def test_rq_endpoint(test_id):
        osf_queue.enqueue(test_rq, test_id)
        return make_response(jsonify({
            'message': 'Job enqueued for scraping.'
        }), 200)

    return facebook_blueprint
