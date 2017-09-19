from osf_scraper_api.utilities.log_helper import _log
from osf.scrapers.facebook import FbScraper
from osf_scraper_api.settings import SELENIUM_URL
from osf_scraper_api.utilities.fs_helper import save_dict, file_exists


def idempotent_scrape_friends(job_name, users, fb_username, fb_password):
    _log('++ starting idempotent scrape friends job')
    fb_scraper = FbScraper(
                    fb_username=fb_username,
                    fb_password=fb_password,
                    command_executor=SELENIUM_URL,
                    log=_log
                )
    fb_scraper.fb_login()

    for user in users:
        key_name = 'jobs/{}/friends/{}.json'.format(job_name, user)
        if file_exists(key_name):
            _log('++ skipping {}'.format(key_name))
            continue
        # otherwise scrape and then save to s3
        output_dict = fb_scraper.get_friends(users=[user])
        save_dict(output_dict, key_name)
        _log('++ data saved to {}'.format(key_name))
    _log('++ request complete')


def idempotent_scrape_posts(job_name, users, fb_username, fb_password, scraper_params):
    _log('++ starting idempotent scrape posts job')
    fb_scraper = FbScraper(
                    fb_username=fb_username,
                    fb_password=fb_password,
                    command_executor=SELENIUM_URL,
                    log=_log
                )
    fb_scraper.fb_login()

    for user in users:
        key_name = 'jobs/{}/posts/{}.json'.format(job_name, user)
        if file_exists(key_name):
            _log('++ skipping {}'.format(key_name))
            continue
        # otherwise scrape and then save to s3
        scraper_params['users'] = [user]
        output_dict = fb_scraper.get_posts(scraper_params)
        save_dict(output_dict, key_name)
        _log('++ data saved to {}'.format(key_name))
    _log('++ request complete')