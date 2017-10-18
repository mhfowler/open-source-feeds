import json

from rq import get_current_job

from osf_scraper_api.utilities.rq_helper import get_rq_jobs_for_user, enqueue_job
from osf_scraper_api.utilities.log_helper import _log, _capture_exception


def test_job(fb_username):
    print fb_username
    rq_jobs = get_rq_jobs_for_user(fb_username=fb_username)
    current_job = get_current_job()

    def filter_fun(job):
        if job.func_name == 'osf_scraper_api.crawler.test_job.test_job':
            if job.kwargs.get('fb_username') == fb_username:
                if not current_job or current_job.id != job.id:
                    return True
        # otherwise return False
        return False

    pending = filter(filter_fun, rq_jobs)
    # if no pending job found, then make request to start pdf job
    if len(pending) == 0:
        _log('++ found no pending jobs')
    else:
        job_logs = []
        for job in rq_jobs:
            j = {
                'id': job.id,
                'started_at': str(job.started_at)
            }
            job_logs.append(j)
        _log('++ found {} pending jobs, waiting for other jobs to finish {} | current_job: {}'.format(
            len(pending),
            json.dumps(job_logs),
            current_job.job_id if current_job else None
        ))