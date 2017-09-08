from flask import Blueprint, render_template

from osf_dashboard.utilities.log_helper import _log
from osf_dashboard.web.extensions import db
from osf_dashboard.settings import TEMPLATE_DIR
from osf_dashboard.utilities.create_test_object import create_test_object, get_test_objects


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

    @helpers_blueprint.route('/api/test_db/')
    def test_db_page():
        """
        this helper page confirms that the database is connected and working
        :return:
        """
        create_test_object(db.session)
        test_objects = get_test_objects(db.session)
        return render_template("hello_db.html", test_objects=test_objects)

    # finally return blueprint
    return helpers_blueprint

