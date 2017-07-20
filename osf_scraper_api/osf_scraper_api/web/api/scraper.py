from flask import make_response, jsonify, Blueprint, request
from osf_scraper_api.web.jobs.scrape_posts import scrape_posts
from osf_scraper_api.web.jobs.test_rq import test_rq

from osf_scraper_api.settings import TEMPLATE_DIR


def get_scraper_blueprint(osf_queue):
    scraper_blueprint = Blueprint('scraper_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @scraper_blueprint.route('/api/test_rq/<test_id>/', methods=['GET'])
    def test_rq_endpoint(test_id):
        osf_queue.enqueue(test_rq, test_id)
        return make_response(jsonify({
            'message': 'Job enqueued for scraping.'
        }), 200)

    @scraper_blueprint.route('/api/scrape_posts/', methods=['PUT'])
    def scrape_posts_endpoint():
        params = request.get_json()
        osf_queue.enqueue(scrape_posts, params)
        return make_response(jsonify({
            'message': 'Job enqueued for scraping.'
        }), 200)

    return scraper_blueprint
