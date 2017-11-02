import datetime
import requests
import time

from flask import g

from osf_scraper_api.utilities.log_helper import _log, _log_image
from osf_scraper_api.utilities.fs_helper import save_dict, load_dict, file_exists
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


def convert_js_date_to_datetime(moment):
    date_str = moment['_d']
    if '+' in date_str:
        splitted = date_str.split('+')
        date_str = splitted[0]
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    return date


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


def check_online():
    try:
        response = requests.get("http://www.google.com")
        if response.status_code == 200:
            return True
    except requests.ConnectionError:
        pass
    # second attempt
    time.sleep(2)
    try:
        response = requests.get("http://www.google.com")
        if response.status_code == 200:
            return True
        return False
    except requests.ConnectionError:
        return False


def save_last_uptime(uptime):
    output_key = 'uptime.json'
    save_dict({
        'uptime': uptime
    }, output_key)


def load_last_uptime():
    try:
        if g.last_uptime:
            return g.last_uptime
    except:
        pass
    output_key = 'uptime.json'
    if file_exists(output_key):
        data_dict = load_dict(output_key)
        return data_dict['uptime']
    else:
        now = int(time.time())
        save_last_uptime(now)
        return now