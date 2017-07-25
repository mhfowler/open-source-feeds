"""
initializes extensions which are then configured in create_app()
based on the Flask factory pattern (http://flask.pocoo.org/docs/0.12/patterns/appfactories/)
"""
from raven.contrib.flask import Sentry
from flask_mail import Mail

# sentry
sentry = Sentry()

# for sending emails
mail = Mail()