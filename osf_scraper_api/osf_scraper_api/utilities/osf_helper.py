import datetime

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from osf_scraper_api.utilities.log_helper import _log, _log_image
from osf.scrapers.facebook import FbScraper
from osf_scraper_api.settings import SELENIUM_URL, ENV_DICT


def get_fb_scraper(fb_username, fb_password):
    # driver = webdriver.PhantomJS(executable_path='/usr/local/lib/node_modules/phantomjs/lib/phantom/bin/phantomjs')

    fb_scraper = FbScraper(
        fb_username=fb_username,
        fb_password=fb_password,
        which_driver='phantomjs',
        log=_log,
        log_image=_log_image,
        dpr=ENV_DICT.get('DPR', 1),
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