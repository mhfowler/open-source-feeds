import json
import time
import os

from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf.scrapers.facebook import FbScraper
from osf_scraper_api.utilities.email_helper import send_email
from osf_scraper_api.settings import SELENIUM_URL, DATA_DIR


def scraper_job(method, params):
    scraper = OsfScraper(params)
    try:
        output = scraper.scrape_helper(method=method)
        scraper.write_output(output)
    except Exception as e:
        _capture_exception(e)
        scraper.send_error_message()


class OsfScraper:

    def __init__(self, params):
        self.params = params
        self.send_to = params.get('send_to')

    def write_output(self, output):
        if self.send_to:
            # if there was an error internally, then don't send output, just send an error message
            _log('++ emailing results to: {}'.format(self.send_to))
            # write the results to a temporary file
            tmp_name = '{}-{}.json'.format(self.send_to, int(time.time()))
            attachment_path = os.path.join(DATA_DIR, tmp_name)
            with open(attachment_path, 'w') as f:
                f.write(json.dumps(output))
            # email the file to the user as an attachment
            t_vars = {}
            send_email(
                to_email=self.send_to,
                subject='Open Source Feeds: Facebook',
                template_path='emails/osf_results.html',
                template_vars=t_vars,
                attachment_path=attachment_path
            )
        else:
            _log('++ output: {}'.format(json.dumps(output)))

    def send_error_message(self, error_message=None):
        if self.send_to:
            _log('++ sending error message to: {}'.format(self.send_to))
            t_vars = {}
            send_email(
                to_email=self.send_to,
                subject='OSF Error',
                template_path='emails/osf_error.html',
                template_vars=t_vars
            )
        else:
            _log('++ error: {}'.format(error_message))

    def scrape_helper(self, method):

        # store output that will be returned
        output = {}

        # iterate through services, and scrape for each of them
        sources = self.params['sources']
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
                    if method == 'posts':
                        fb_output = fb_scraper.get_posts({
                            'users': s_params['users']
                        })
                    elif method == 'friends':
                        fb_output = fb_scraper.get_friends(users=s_params['users'])
                    else:
                        raise Exception('++ invalid facebook method: {}'.format(method))
                    # store the output to this dictionary
                    output['facebook'] = fb_output
                except Exception as e:
                    _capture_exception(e)
                    # for the email version, abort on errors here
                    if self.send_to:
                        self.send_error_message()
                    # but for backend version, keep going
                    output['facebook'] = 'Error'
                finally:
                    # quit driver
                    fb_scraper.quit_driver()
            else:
                raise Exception('++ invalid scraping service')

        # return output
        return output