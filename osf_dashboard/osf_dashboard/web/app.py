import rq_dashboard
from flask import Flask, Response, request, render_template

from osf_dashboard.settings import PROJECT_PATH, TEMPLATE_DIR, ENV_DICT, get_db_url
from osf_dashboard.utilities.log_helper import _log, _capture_exception
from osf_dashboard.web.api.helper import get_helpers_blueprint
from osf_dashboard.web.extensions import sentry, mail, db
from osf_dashboard.web.flask_admin_routes import get_flask_admin


# create flask app
def create_app():
    _log('++ using environ: {}'.format(ENV_DICT['ENVIRON']))

    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=PROJECT_PATH)
    app.config.from_object(rq_dashboard.default_settings)
    app.config.update(
        DEBUG=ENV_DICT.get('FLASK_DEBUG') or False,
        SECRET_KEY=ENV_DICT['FLASK_SECRET_KEY']
    )

    # initialize sql alchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
    db.init_app(app)

    # initialize flask-admin
    admin = get_flask_admin()
    admin.init_app(app)

    # initialize flask-mail
    mail_keys = [
        "MAIL_SERVER",
        "MAIL_PORT",
        "MAIL_USE_TLS",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_DEFAULT_SENDER"
    ]
    for key in mail_keys:
        app.config[key] = ENV_DICT[key]
    mail.init_app(app)

    # register blueprints
    app.register_blueprint(get_helpers_blueprint())

    # configure sentry
    if ENV_DICT.get('SENTRY_DSN'):
        _log('++ using Sentry for error logging')
        sentry.init_app(app, dsn=ENV_DICT['SENTRY_DSN'])

    @app.route('/api/hello/')
    def hello_page():
        return render_template('hello.html')

    @app.errorhandler(Exception)
    def error_handler(e):
        """
        if a page throws an error, log the error to slack, and then re-raise the error
        """
        _capture_exception(e)
        # re-raise error
        raise e

    # return the app
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5001, use_reloader=False)
