import random

from redis import StrictRedis
from rq import Queue
from rq.job import Job
from redis import Redis
from rq.registry import StartedJobRegistry

from osf_scraper_api.settings import ENV_DICT, DEFAULT_JOB_TIMEOUT


def enqueue_job(*args, **kwargs):
    fb_username = kwargs['fb_username']
    job_fun = args[0]
    queue = get_queue_for_user(fb_username)
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
        job = Job.fetch(job_id, connection=redis_conn)
        jobs.append(job)
    return jobs


def get_rq_jobs(queue_name):
    osf_queue = get_osf_queue(queue_name)
    queue_jobs = osf_queue.jobs
    running_jobs = get_running_rq_jobs(queue_name)
    all_jobs = queue_jobs + running_jobs
    return all_jobs


def str_to_probability(in_str):
    """Return a reproducible uniformly random float in the interval [0, 1) for the given seed."""
    return random.Random(in_str).randint(0, len(ENV_DICT['QUEUE_NAMES']))


def get_queue_name(fb_username):
    map = {
        'happyrainbows93@yahoo.com': 'osf0',
        'maxhfowler@gmail.com': 'osf1'
    }
    if map.get(fb_username):
        return map[fb_username]
    index = str_to_probability(fb_username)
    queue_name = ENV_DICT['QUEUE_NAMES'][index]
    return queue_name


def get_queue_for_user(fb_username):
    queue_map = get_queue_map()
    queue_name = get_queue_name(fb_username)
    queue = queue_map[queue_name]
    return queue


if __name__ == '__main__':
    queue_name = get_queue_name(fb_username='maxhfowler@gmail.com')
    jobs = get_rq_jobs(queue_name)
    for job in jobs:
        print job.func_name