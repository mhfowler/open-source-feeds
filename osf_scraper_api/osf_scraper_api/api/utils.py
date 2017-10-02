from flask import make_response, jsonify, Blueprint, request, abort

from osf_scraper_api.settings import TEMPLATE_DIR
from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.selenium_helper import restart_selenium
from osf_scraper_api.jobs.test_rq import test_rq


def get_utils_blueprint(osf_queue):
    utils_blueprint = Blueprint('utils_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @utils_blueprint.route('/api/restart_selenium/', methods=['GET'])
    def restart_selenium_endpoint():
        _log('++ received post to restart selenium endpoint')
        restart_selenium()
        return make_response(jsonify({
            'message': '++ restarted selenium'
        }), 200)

    @utils_blueprint.route('/api/test_rq/<test_id>/', methods=['GET'])
    def test_rq_endpoint(test_id):
        osf_queue.enqueue(test_rq, test_id)
        return make_response(jsonify({
            'message': 'Job enqueued for scraping.'
        }), 200)

    return utils_blueprint
