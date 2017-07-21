import json

from osf_scraper_api.utilities.log_helper import _log
from osf.scrapers.facebook import FbScraper


def scrape_posts(params):

    # store output that will be returned
    output = {}

    # iterate through services, and scrape for each of them
    sources = params['sources']
    for source, s_params in sources.items():
        _log('++ scraping source: {}'.format(source))
        if source == 'facebook':
            # log params
            for key, val in s_params.items():
                if key != 'password':
                    _log('{}: {}'.format(key, val))
            # scrape posts
            fb_scraper = FbScraper(params=s_params, log=_log)
            fb_output = fb_scraper.fb_scrape_posts()
            # store the output to this dictionary
            output['facebook'] = fb_output
        else:
            raise Exception('++ invalid scraping service')

    # write output in correct location
    if params['output'] == 'file':
        output_path = params['output_path']
        with open(output_path, 'w') as f:
            # TODO: remove this slack log
            _log('++ output: {}'.format(json.dumps(output)))
            f.write(json.dumps(output))
    else:
        raise Exception('++ invalid output format')


