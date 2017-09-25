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
        dpr=ENV_DICT.get('DPR', 1)
    )
    return fb_scraper