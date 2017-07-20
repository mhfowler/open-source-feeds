import json

from osf_scraper_api.utilities.log_helper import _log
from osf_scrapers.facebook.facebook_scrape import FbScraper


def scrape_posts(params):

    # iterate through services, and scrape for each of them
    for service, s_params in params.items():
        _log('++ scraping service: {}'.format(service))
        if service == 'facebook':
            for key, val in s_params.items():
                if key != 'password':
                    _log('{}: {}'.format(key, val))
            fb_scraper = FbScraper(s_params)
            fb_scraper.fb_scrape_posts()


