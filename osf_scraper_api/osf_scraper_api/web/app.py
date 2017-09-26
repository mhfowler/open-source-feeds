import rq_dashboard
from flask import Flask, Response, request, render_template
from redis import StrictRedis
from rq import Queue

from osf_scraper_api.api.facebook import get_facebook_blueprint
from osf_scraper_api.api.helper import get_helpers_blueprint
from osf_scraper_api.crawler.crawler_api import get_crawler_blueprint
from osf_scraper_api.settings import PROJECT_PATH, TEMPLATE_DIR, ENV_DICT, DEFAULT_JOB_TIMEOUT
from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.web.extensions import sentry, mail


# create flask app
def create_app():
    _log('++ using environ: {}'.format(ENV_DICT['ENVIRON']))

    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=PROJECT_PATH)
    app.config.from_object(rq_dashboard.default_settings)
    app.config.update(
        DEBUG=ENV_DICT.get('FLASK_DEBUG') or False,
        SECRET_KEY=ENV_DICT['FLASK_SECRET_KEY'],
        REDIS_HOST=ENV_DICT.get('REDIS_HOST'),
        REDIS_PORT=ENV_DICT.get('REDIS_PORT'),
        REDIS_DB=ENV_DICT.get('REDIS_DB'),
        REDIS_PASSWORD=ENV_DICT.get('REDIS_PASSWORD')
    )

    redis_connection = StrictRedis(
        host=ENV_DICT.get('REDIS_HOST'),
        port=ENV_DICT.get('REDIS_PORT'),
        db=ENV_DICT.get('REDIS_DB'),
        password=ENV_DICT.get('REDIS_PASSWORD')
    )
    osf_queue = Queue('osf', connection=redis_connection, default_timeout=DEFAULT_JOB_TIMEOUT)

    # add basic auth to rq_dashboard blueprint
    @rq_dashboard.blueprint.before_request
    def rq_dashboard_basic_auth(*args, **kwargs):
        auth = request.authorization
        username = ENV_DICT.get('RQ_DASHBOARD_USERNAME')
        password = ENV_DICT.get('RQ_DASHBOARD_PASSWORD')
        if auth is None or auth.username != username or auth.password != password:
            return Response(
                'Please login',
                401,
                {'WWW-Authenticate': 'Basic realm="RQ Dashboard"'}
            )

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
    app.register_blueprint(get_facebook_blueprint(osf_queue))
    app.register_blueprint(get_crawler_blueprint(osf_queue))
    app.register_blueprint(rq_dashboard.blueprint, url_prefix='/rq')

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
    app.run(port=5002, use_reloader=False)
