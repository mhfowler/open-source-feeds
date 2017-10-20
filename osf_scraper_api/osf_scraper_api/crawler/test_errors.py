import random

from flask import make_response, jsonify, Blueprint

from osf_scraper_api.settings import TEMPLATE_DIR
from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.rq_helper import enqueue_job


def error_job(number):
    val = random.random()
    _log('++ {} val: {}'.format(number, val))
    if val < 0.5:
        raise Exception('++ error: {} | {}'.format(number, val))
    return True


def get_test_errors_blueprint():
    test_errors_blueprint = Blueprint('test_errors_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @test_errors_blueprint.route('/api/test_errors/', methods=['GET'])
    def whats_on_your_mind_endpoint():
        _log('++ new request to test errors')
        for i in range(0, 20):
            enqueue_job(error_job, number=i)
        return make_response(jsonify({
            'message': "started"
        }), 200)

    return test_errors_blueprint
