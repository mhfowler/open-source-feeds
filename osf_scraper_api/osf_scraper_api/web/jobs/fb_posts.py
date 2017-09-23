import json
import time
import os
import datetime

from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf.scrapers.facebook import FbScraper
from osf_scraper_api.utilities.email_helper import send_email
from osf_scraper_api.settings import SELENIUM_URL, DATA_DIR
from osf_scraper_api.utilities.fs_helper import save_dict


def scrape_fb_posts(params):
    _log('++ starting fb_posts job')
    scraper = OsfScraper(params)
    try:
        output = scraper.scrape_fb_posts()
        scraper.write_output(output)
        _log('++ request complete')
    except Exception as e:
        _capture_exception(e)
        scraper.send_error_message()


class OsfScraper:

    def __init__(self, params):
        self.params = params
        self.send_to = params.get('send_to')
        # if replace=false then it creates a new file within the folder located at output_path
        # if replace=true, then it replaces output_path with the output contents
        self.replace = params.get('replace') is True
        self.time = int(time.time())

    def convert_timestamp_to_date(self, ts):
        try:
            return datetime.datetime.fromtimestamp(int(ts))
        except:
            _log('++ warning: unable to parse timestamp {}'.format(ts))
            return None

    def write_output(self, output):
        # save the output to the fs
        if not self.replace:
            # TODO: assert output_folder does not exist or is a folder
            output_folder = self.params['output_folder']
            f_name = '{}.json'.format(self.time)
            f_path = '{}/{}'.format(output_folder, f_name)
        # otherwise, its a replace
        else:
            # TODO: assert output_path does not exist or is a file
            f_path = self.params.get('output_path')
        _log('++ saving results to: {}'.format(f_path))
        save_dict(data_dict=output, destination=f_path)
        # other forms of optional output
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
        elif self.params.get('log_to_slack'):
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

    def scrape_fb_posts(self):

        # store output that will be returned
        s_params = self.params

        # log params
        for key, val in s_params.items():
            if key != 'fb_password':
                _log('++ param[{}]: {}'.format(key, val))
        # initialize scraper
        fb_scraper = FbScraper(
            fb_username=s_params['fb_username'],
            fb_password=s_params['fb_password'],
            command_executor=SELENIUM_URL,
            log=_log
        )
        try:
            # parse timestamps if supplied
            after_date = None
            if s_params.get('after_timestamp'):
                after_date = self.convert_timestamp_to_date(s_params.get('after_timestamp'))
            before_date = None
            if s_params.get('before_timestamp'):
                before_date = self.convert_timestamp_to_date(s_params.get('before_timestamp'))
            jump_to = None
            if s_params.get('jump_to_timestamp'):
                jump_to = self.convert_timestamp_to_date(s_params.get('jump_to_timestamp'))
            # then call function
            output = fb_scraper.get_posts({
                'users': s_params['users'],
                'max_num_posts_per_user': s_params.get('max_num_posts_per_user'),
                'after_date': after_date,
                'before_date': before_date,
                'jump_to': jump_to
            })
        except Exception as e:
            _capture_exception(e)
            # for the email version, abort on errors here
            if self.send_to:
                self.send_error_message()
            # but for backend version, keep going
            output = 'Error'
        finally:
            # quit driver
            fb_scraper.quit_driver()

        # return output
        return output