"""
Adapted from https://gist.github.com/spjwebster/6521272
"""
import sys

from redis import StrictRedis
from rq import Worker, Queue, Connection

from osf_scraper_api.settings import ENV_DICT

redis_connection = StrictRedis(
    host=ENV_DICT.get('REDIS_HOST'),
    port=ENV_DICT.get('REDIS_PORT'),
    db=ENV_DICT.get('REDIS_DB'),
    password=ENV_DICT.get('REDIS_PASSWORD')
)
default_max_failures = ENV_DICT.get('RQ_DEFAULT_MAX_JOB_FAILURES', 3)
default_retry_delay = ENV_DICT.get('RQ_DEFAULT_RETRY_DELAY', 60)

queues = None


def retry_handler(job, exc_type, exc_value, traceback):
    # if the job is not marked for retry, fall through to the default
    # exception handler that will move the job to the 'failed' queue
    job.refresh()
    if not job.meta.get('retry'):
        return True


if __name__ == '__main__':
    with Connection(redis_connection):
        queues = map(Queue, sys.argv[1:]) or [Queue()]
        worker = Worker(queues)
        worker.push_exc_handler(retry_handler)
        worker.work()
