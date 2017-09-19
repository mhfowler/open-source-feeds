from flask import make_response, jsonify, Blueprint, request, abort
from osf_scraper_api.web.jobs.scraper import scraper_job
from osf_scraper_api.web.jobs.idempotent import idempotent_scrape_friends, idempotent_scrape_posts
from osf_scraper_api.web.jobs.test_rq import test_rq

from osf_scraper_api.settings import TEMPLATE_DIR


def get_scraper_blueprint(osf_queue):
    scraper_blueprint = Blueprint('scraper_blueprint', __name__, template_folder=TEMPLATE_DIR)

    def scrape_endpoint(method):

        # get params from request
        params = request.get_json()

        # validate parameters
        if 'sources' not in params:
            abort(make_response(jsonify({
                'message': 'Missing required field: sources'
            }), 422))

        sources = params['sources']
        if 'facebook' in sources:
            fb_params = sources['facebook']
            required_fields = ['username', 'password', 'users']
            missing_required_fields = [f for f in required_fields if not fb_params.get(f)]
            if missing_required_fields:
                abort(make_response(jsonify({
                    'message': 'Missing required fields for facebook: {}.'.format(', '.join(missing_required_fields))
                }), 422))

        # enqueue job
        osf_queue.enqueue(scraper_job, method=method, params=params)

        # return response
        if 'send_to' in params:
            msg = 'Job enqueued for scraping. Results will be emailed to: {}'.format(params.get('send_to'))
        else:
            msg = 'Job enqueued for scraping but no email was provided. If you would like to be emailed the results' \
                  'please add a send_to field to the request.'

        return make_response(jsonify({
            'message': msg
        }), 200)

    @scraper_blueprint.route('/api/test_rq/<test_id>/', methods=['GET'])
    def test_rq_endpoint(test_id):
        osf_queue.enqueue(test_rq, test_id)
        return make_response(jsonify({
            'message': 'Job enqueued for scraping.'
        }), 200)

    @scraper_blueprint.route('/api/scrape_posts/', methods=['POST'])
    def scrape_posts_endpoint():
        return scrape_endpoint(method='posts')

    @scraper_blueprint.route('/api/scrape_friends/', methods=['POST'])
    def scrape_friends_endpoint():
        return scrape_endpoint(method='friends')

    @scraper_blueprint.route('/api/idempotent/friends/', methods=['POST'])
    def idempotent_friends_endpoint():
        params = request.get_json()
        idempotent_scrape_friends(
            job_name=params['job_name'],
            users=params['users'],
            fb_username=params['fb_username'],
            fb_password=params['fb_password']
        )
        return make_response(jsonify({
            'message': 'Ok'
        }), 200)

    @scraper_blueprint.route('/api/idempotent/posts/', methods=['POST'])
    def idempotent_posts_endpoint():
        params = request.get_json()
        idempotent_scrape_posts(
            job_name=params['job_name'],
            users=params['users'],
            fb_username=params['fb_username'],
            fb_password=params['fb_password'],
            scraper_params=params['scraper_params']
        )
        return make_response(jsonify({
            'message': 'Ok'
        }), 200)

    return scraper_blueprint
