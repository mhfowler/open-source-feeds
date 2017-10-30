import json
import time
import os
import datetime


from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.osf_helper import get_fb_scraper, wait_for_online, check_online
from osf_scraper_api.utilities.email_helper import send_email
from osf_scraper_api.settings import DATA_DIR
from osf_scraper_api.utilities.fs_helper import save_dict, file_exists
from osf_scraper_api.electron.utils import save_current_pipeline, load_current_pipeline
from osf_scraper_api.utilities.selenium_helper import restart_selenium
from osf_scraper_api.utilities.rq_helper import get_all_rq_jobs


def scrape_fb_posts_job(users, output_folder, scraper_params, fb_username, fb_password):
    _log('++ starting scrape_fb_posts_job')
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    num_users = len(users)
    for index, user in enumerate(users):
        try:
            f_name = '{}.json'.format(user)
            output_path = os.path.join(output_folder, f_name)
            if file_exists(output_path):
                _log('++ skipping {}'.format(user))
                continue
            scraper_params['users'] = [user]
            _log('++ scraping fb_posts for user {} [{}/{}]'.format(user, index, num_users))
            output = scrape_fb_posts(scraper_params, output_path=output_path, fb_scraper=fb_scraper)
            fb_scraper.num_initializations = 0
        except Exception as e:
            _capture_exception(e)
            continue
    # finally, quit
    _log('++ request complete')
    fb_scraper.quit_driver()


def fb_posts_post_process():
    _log('++ running post process check for pending fb_posts jobs')
    # check if there are any other pending scrape_posts jobs for this user
    rq_jobs = get_all_rq_jobs()
    def filter_fun(job):
        if job.func_name == 'osf_scraper_api.electron.fb_posts.scrape_fb_posts_job':
            return True
        # otherwise return False
        return False
    pending = filter(filter_fun, rq_jobs)
    # if no jobs found, then pipeline is complete
    if len(pending) == 0:
        _log('++ scrape fb posts pipeline finished')
        finished_pipeline = load_current_pipeline()
        pipeline_params = finished_pipeline['pipeline_params']
        save_current_pipeline(
            pipeline_name='fb_posts',
            pipeline_status='finished',
            pipeline_params=finished_pipeline['pipeline_params'],
            pipeline_message=pipeline_params['output_folder']
        )
    else:
        _log('++ found {} pending jobs, continuing fb posts pipeline'.format(len(pending)))


def scrape_fb_posts(params, output_path, fb_scraper=None, num_attempts=0):
    scraper = OsfScraper(params, fb_scraper=fb_scraper)
    try:
        output = scraper.scrape_fb_posts()
        is_online = check_online()
        if not is_online:
            raise Exception('++ disconnected from the internet')
        save_dict(output, output_path)
        # if successful then set num to 0
        fb_scraper.num_initializations = 0
    except Exception as e:
        _log('++ encountered error {}'.format(str(e)))
        wait_for_online()
        if num_attempts == 0:
            restart_selenium()
            fb_scraper.re_initialize_driver()
            num_attempts += 1
            return scrape_fb_posts(params=params, fb_scraper=fb_scraper, num_attempts=num_attempts)
        else:
            restart_selenium()
            fb_scraper.re_initialize_driver()
            raise e


class OsfScraper:

    def __init__(self, params, fb_scraper=None):
        self.params = params
        self.send_to = params.get('send_to')
        # if replace=false then it creates a new file within the folder located at output_path
        # if replace=true, then it replaces output_path with the output contents
        self.replace = params.get('replace') is True
        self.time = int(time.time())
        self.fb_scraper = fb_scraper

    def convert_timestamp_to_date(self, ts):
        try:
            return datetime.datetime.fromtimestamp(int(ts))
        except:
            _log('++ warning: unable to parse timestamp {}'.format(ts))
            return None

    def quit_driver(self):
        if self.fb_scraper:
            self.fb_scraper.quit_driver()

    def write_output(self, output):
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
        # for key, val in s_params.items():
        #     if key != 'fb_password':
        #         _log('++ param[{}]: {}'.format(key, val))
        # initialize scraper
        if not self.fb_scraper:
            self.fb_scraper = get_fb_scraper(s_params['fb_username'], fb_password=s_params['fb_password'])

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
        output = self.fb_scraper.get_posts({
            'users': s_params['users'],
            'max_num_posts_per_user': s_params.get('max_num_posts_per_user'),
            'after_date': after_date,
            'before_date': before_date,
            'jump_to': jump_to
        })

        # return output
        return output
