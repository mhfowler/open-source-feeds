import requests
import json

from osf_scraper_api.utilities.osf_helper import get_fb_scraper
from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.utilities.email_helper import send_email


def whats_on_your_mind_job(fb_username, fb_password):
    try:
        fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
        user = fb_scraper.get_currently_logged_in_user()
        _log('++ successfully looked up currently logged in user: {}'.format(user))
        job_params = {
            'users': [user],
            'post_process': True,
            'fb_username': fb_username,
            'fb_password': fb_password
        }
        url = '{API_DOMAIN}/api/crawler/fb_friends/'.format(API_DOMAIN=ENV_DICT['API_DOMAIN'])
        _log('++ making post request to {}'.format(url))
        headers = {'content-type': 'application/json'}
        requests.post(url, data=json.dumps(job_params), headers=headers)
    except Exception as e:
        _log('++ /api/whats_on_your_mind/ failed to login')
        send_email(
            to_email=fb_username,
            subject='Open Source Feeds',
            template_path='emails/whats_on_your_mind.html',
            template_vars={}
        )
        raise e
