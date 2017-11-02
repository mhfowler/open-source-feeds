import random

from redis import StrictRedis
from rq import Queue, get_failed_queue
from rq.job import Job
from rq.worker import Worker
from redis import Redis
from rq.registry import StartedJobRegistry

from osf_scraper_api.settings import ENV_DICT, DEFAULT_JOB_TIMEOUT
from osf_scraper_api.utilities.log_helper import _log, _capture_exception


def enqueue_job(*args, **kwargs):
    fb_username = kwargs.get('fb_username')
    if fb_username:
        queue = get_queue_for_user(fb_username)
    else:
        queue_name = ENV_DICT['QUEUE_NAMES'][0]
        queue = get_osf_queue(queue_name)
    job_fun = args[0]
    return queue.enqueue(job_fun, **kwargs)


def get_redis_connection():
    redis_connection = StrictRedis(
        host=ENV_DICT.get('REDIS_HOST'),
        port=ENV_DICT.get('REDIS_PORT'),
        db=ENV_DICT.get('REDIS_DB'),
        password=ENV_DICT.get('REDIS_PASSWORD')
    )
    return redis_connection


def get_osf_queue(queue_name):
    redis_connection = get_redis_connection()
    osf_queue = Queue(queue_name, connection=redis_connection, default_timeout=DEFAULT_JOB_TIMEOUT)
    return osf_queue


def get_queue_map():
    queue_map = {}
    for queue_name in ENV_DICT['QUEUE_NAMES']:
        queue = get_osf_queue(queue_name=queue_name)
        queue_map[queue_name] = queue
    return queue_map


def get_rq_jobs_for_user(fb_username):
    queue_name = get_queue_name(fb_username=fb_username)
    return get_rq_jobs(queue_name=queue_name)


def get_running_rq_jobs(queue_name):
    redis_conn = get_redis_connection()
    registry = StartedJobRegistry(queue_name, connection=redis_conn)
    running_job_ids = registry.get_job_ids() # Jobs which are exactly running.
    jobs = []
    for job_id in running_job_ids:
        try:
            job = Job.fetch(job_id, connection=redis_conn)
            jobs.append(job)
        except:
            continue
    return jobs


def get_failed_jobs():
    failed_queue = get_osf_queue('failed')
    failed_jobs = failed_queue.jobs
    return failed_jobs


def get_rq_jobs(queue_name):
    osf_queue = get_osf_queue(queue_name)
    queue_jobs = osf_queue.jobs
    running_jobs = get_running_rq_jobs(queue_name)
    failed_jobs = get_failed_jobs()
    all_jobs = queue_jobs + running_jobs + failed_jobs
    return all_jobs


def get_all_rq_jobs():
    queue_names = ENV_DICT['QUEUE_NAMES']
    all_jobs = []
    for queue_name in queue_names:
        jobs = get_rq_jobs(queue_name)
        all_jobs += jobs
    return all_jobs


def str_to_probability(in_str):
    """Return a reproducible uniformly random float in the interval [0, 1) for the given seed."""
    return random.Random(in_str).randint(0, len(ENV_DICT['QUEUE_NAMES']))


def get_queue_name(fb_username):
    # map = {
    #     'happyrainbows93@yahoo.com': 'osf0',
    #     'maxhfowler@gmail.com': 'osf1'
    # }
    # if map.get(fb_username):
    #     return map[fb_username]
    # index = str_to_probability(fb_username)
    # queue_name = ENV_DICT['QUEUE_NAMES'][index]
    return 'osf0'
    # return queue_name


def get_queue_for_user(fb_username):
    queue_map = get_queue_map()
    queue_name = get_queue_name(fb_username)
    queue = queue_map[queue_name]
    return queue


def clear_old_workers():
    _log('++ clearing old rq workers')
    conn = get_redis_connection()
    for w in Worker.all(conn):
        if w.state != 'busy':
            _log('++ stopping rq worker {}'.format(w.pid))
            w.register_death()


def stop_jobs():
    # TODO: figure out how to stop running jobs
    jobs = get_all_rq_jobs()
    for job in jobs:
        job.delete()


def restart_failed_jobs():
    failed_queue = get_osf_queue('failed')
    new_queue = get_osf_queue(ENV_DICT['QUEUE_NAMES'][0])
    failed_jobs = failed_queue.get_jobs()
    _log('++ restarting any failed jobs')
    for job in failed_jobs:
        try:
            job.refresh()
            failures = job.meta.get('failures', 0) + 1
            max_failures = 5
            if failures >= max_failures:
                _log('++ rq job {func_name} {job_id}: failed too many times times ({num_failures}), deleting'.format(
                    func_name=job.func_name,
                    job_id=str(job.id),
                    num_failures=str(failures)
                ))
                job.delete()
                continue
            else:
                _log('++ requeueing failed job: {} {}, attempt {}'.format(job.func_name, str(job.id), str(failures)))
                job.meta['failures'] = failures
                job.save()
                failed_queue.remove(job)
                new_queue.enqueue_job(job)
        except Exception as e:
            _capture_exception(e)
            pass


if __name__ == '__main__':
    clear_old_workers()
    # queue_name = get_queue_name(fb_username='maxhfowler@gmail.com')
    # jobs = get_rq_jobs(queue_name)
    # for job in jobs:
    #     print job.func_name