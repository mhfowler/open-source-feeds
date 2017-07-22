import json

from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf.scrapers.facebook import FbScraper
from osf_scraper_api.settings import SELENIUM_URL


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
                    _log('++ param[{}]: {}'.format(key, val))
            # scrape posts
            fb_scraper = FbScraper(
                fb_username=s_params['username'],
                fb_password=s_params['password'],
                command_executor=SELENIUM_URL,
                log=_log
            )
            try:
                fb_output = fb_scraper.get_posts({
                    'users': s_params['users']
                })
                # store the output to this dictionary
                output['facebook'] = fb_output
            except Exception as e:
                _capture_exception(e)
                output['facebook'] = None
            finally:
                # quit driver
                fb_scraper.quit_driver()
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


def scrape_friends(params):

    # store output that will be returned
    output = {}

    # iterate through services, and scrape for each of them
    _log('++ scraping friends of: {}'.format(params['user']))
    # scrape friends
    fb_scraper = FbScraper(
        fb_username=params['username'],
        fb_password=params['password'],
        command_executor=SELENIUM_URL,
        log=_log
    )
    try:
        fb_output = fb_scraper.get_friends(user=params['user'])
        # store the output to this dictionary
        output['friends'] = fb_output
    except Exception as e:
        _capture_exception(e)
        output['facebook'] = None
    finally:
        # quit driver
        fb_scraper.quit_driver()

    # write output in correct location
    if params['output'] == 'file':
        output_path = params['output_path']
        with open(output_path, 'w') as f:
            # TODO: remove this slack log
            _log('++ output: {}'.format(json.dumps(output)))
            f.write(json.dumps(output))
    else:
        raise Exception('++ invalid output format')