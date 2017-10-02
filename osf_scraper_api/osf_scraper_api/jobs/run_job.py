import time

from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.fs_helper import save_dict
from osf_scraper_api.jobs.scrape_fb_posts import scrape_fb_posts
from osf_scraper_api.jobs.scrape_fb_friends import scrape_fb_friends


def run_job(job_type, job_params, fb_username, output_bin):

    # log that job is starting
    _log('++ starting {} job'.format(job_type))

    # log params
    log_params = {}
    for key, val in job_params.items():
        if key != 'fb_password':
            log_params[key] = val
            _log('++ param[{}]: {}'.format(key, val))

    # choose which job to run
    job_funs = {
        'scrape_fb_posts': scrape_fb_posts,
        'scrape_fb_friends': scrape_fb_friends,
    }
    job_fun = job_funs[job_type]

    # run the job
    try:
        data_dict = job_fun(**job_params)
        # format the output
        timestamp = int(time.time())
        output_dict = {
            'job_type': job_type,
            'job_params': log_params,
            'created_at': timestamp,
            'data': data_dict
        }
    except Exception as e:
        # if there was an error, then still write the output, but with the error message
        _capture_exception(e)
        timestamp = int(time.time())
        output_dict = {
            'job_type': job_type,
            'job_params': log_params,
            'created_at': timestamp,
            'error': e.message
        }

    # save the output to the bin (with a filename of the current time)
    output_path = 'output/{}/{}.json'.format(output_bin, timestamp)
    _log('++ saving results to: {}'.format(output_path))
    save_dict(data_dict=output_dict, destination=output_path)
