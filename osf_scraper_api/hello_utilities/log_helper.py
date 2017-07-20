import traceback
import sys

from hello_utilities.slack_helper import slack_notify_message
from hello_settings import ENV_DICT
from hello_webapp.extensions import sentry


def _log(message, channel_name=None):
    """
    instead of using print, call this function, and then handle behavior based on environment appropriately
    :param message: string to log
    :param channel_name: string name of slack channel to log message to (this channel must exist)
    -- note that a suffix may be appended to this channel name automatically SLACK_CHANNEL_SUFFIX is in env.json
    :return: None
    """
    print message

    # if slack logging is turned on
    if ENV_DICT.get('LOG_TO_SLACK'):
        slack_notify_message(message, channel_name=channel_name)


def _capture_exception(e):
    """
    wrapper function which uses sentry to captureException if sentry is enabled in this environment
    :param e: exception to be captured
    :return: None
    """
    # log exception to slack
    exc_type, exc_value, exc_traceback = sys.exc_info()
    formatted_lines = traceback.format_exc()
    _log('@channel: error: {}'.format(e.message), channel_name='_error')
    _log(formatted_lines, channel_name='_error')
    if ENV_DICT.get('SENTRY_DSN'):
        sentry.captureException()
