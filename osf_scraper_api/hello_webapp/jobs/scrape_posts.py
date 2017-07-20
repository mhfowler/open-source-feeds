import json
from hello_utilities.log_helper import _log


def scrape_posts(params):
    _log('++ scraping posts: {}'.format(json.dumps(params)))
