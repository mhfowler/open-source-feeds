import datetime
import requests
import time

from osf_scraper_api.utilities.log_helper import _log, _log_image
from osf.scrapers.facebook import FbScraper
from osf_scraper_api.settings import SELENIUM_URL, ENV_DICT


def get_fb_scraper(fb_username, fb_password):
    fb_scraper = FbScraper(
        fb_username=fb_username,
        fb_password=fb_password,
        command_executor=SELENIUM_URL,
        log=_log,
        log_image=_log_image,
        dpr=ENV_DICT.get('DPR', 1),
        proxy=ENV_DICT.get('PROXY')
    )
    return fb_scraper


def paginate_list(mylist, page_size):
    return [mylist[i:i + page_size] for i in range(0, len(mylist), page_size)]


def convert_timestamp_to_date(ts):
    if not ts:
        return None
    try:
        return datetime.datetime.fromtimestamp(int(ts))
    except:
        _log('++ warning: unable to parse timestamp {}'.format(ts))
        return None


def wait_for_online():
    online = False
    while not online:
        try:
            response = requests.get("http://www.google.com")
            if response.status_code == 200:
                online = True
        except requests.ConnectionError:
            _log('++ waiting for internet connection')
            time.sleep(1)
    return True
