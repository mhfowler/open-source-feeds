from flask import Blueprint

from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.email_helper import send_email
from osf_scraper_api.settings import TEMPLATE_DIR


def get_helpers_blueprint():

    # blueprint for these routes
    helpers_blueprint = Blueprint('helpers_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @helpers_blueprint.route('/api/error/')
    def flask_force_error():
        """
        this helper page forces an error, for testing error logging
        """
        raise Exception('forced 500 error')

    @helpers_blueprint.route('/api/slack/')
    def flask_slack_test():
        """
        this helper page for testing if slack is working
        """
        _log('@channel: slack is working?')
        return 'slack test'

    @helpers_blueprint.route('/api/email/')
    def flask_email_test():
        """
        this helper page for testing if slack is working
        """
        _log('++ sending test email')
        send_email(
            to_email='maxhfowler@gmail.com',
            subject='OSF is running',
            template_path='emails/test_email.html',
            template_vars={}
        )
        return 'email sent'

    # finally return blueprint
    return helpers_blueprint

