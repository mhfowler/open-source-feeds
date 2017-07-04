from flask import Blueprint

from hello_utilities.log_helper import _log


def get_hello_helpers_blueprint(template_dir):

    # blueprint for these routes
    hello_helpers = Blueprint('hello_helpers', __name__, template_folder=template_dir)

    @hello_helpers.route('/error/')
    def flask_force_error():
        """
        this helper page forces an error, for testing error logging
        """
        raise Exception('forced 500 error')

    @hello_helpers.route('/slack/')
    def flask_slack_test():
        """
        this helper page for testing if slack is working
        """
        _log('@channel: slack is working?')
        return 'slack test'

    # finally return blueprint
    return hello_helpers

