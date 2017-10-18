import sys
import traceback
import random
import os

from osf_scraper_api.utilities.slack_helper import slack_notify_message
from osf_scraper_api.web.extensions import sentry
from osf_scraper_api.settings import ENV_DICT


def _log(message, channel_name=None):
    """
    instead of using print, call this function, and then handle behavior based on environment appropriately
    :param message: string to log
    :param channel_name: string name of slack channel to log message to (this channel must exist)
    -- note that a suffix may be appended to this channel name automatically SLACK_CHANNEL_SUFFIX is in env.json
    :return: None
    """
    if message.startswith('++'):
        if ENV_DICT.get('HOST_IP_ADDRESS'):
            message = message[2:]   # remove prefix
            message = '++ [{}]'.format(ENV_DICT.get('HOST_IP_ADDRESS')) + message
    print message

    # if slack logging is turned on
    if ENV_DICT.get('LOG_TO_SLACK'):
        slack_notify_message(message, channel_name=channel_name)

    # if fs logging is turned on
    if ENV_DICT.get('FS_LOG_PATH'):
        f_path = ENV_DICT['FS_LOG_PATH']
        with open(f_path, 'a') as f:
            f.write(message + '\n')


def _log_image(image_path):
    from osf_scraper_api.utilities.s3_helper import s3_upload_file
    s3_key = 'debug/{}.png'.format(random.randint(0, 1000000))
    image_url = s3_upload_file(source_file_path=image_path, destination=s3_key)
    _log('++ debug: {}'.format(image_url))


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


def _capture_rq_exception(exc_type, exc_value, exc_traceback):
    """
    rq exception doesn't provide exception object, so we use these values instead
    :return: None
    """
    # log exception to slack
    formatted_lines = traceback.format_exc()
    _log('@channel: error: {}'.format(exc_value), channel_name='_error')
    _log(formatted_lines, channel_name='_error')
    if ENV_DICT.get('SENTRY_DSN'):
        sentry.captureException()


if __name__ == '__main__':
    _log('test')