"""
Adapted from https://gist.github.com/spjwebster/6521272
"""
import sys

from redis import StrictRedis
from rq import Worker, Queue, Connection

from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.utilities.log_helper import _capture_rq_exception

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
    # try to log the exception
    try:
        _capture_rq_exception(exc_type=exc_type, exc_value=exc_value, exc_traceback=traceback)
    except:
        pass
    # and then regardless, return True, such that exception gets passed
    # to the next handler which puts it in the failed queue
    job.refresh()
    return True


if __name__ == '__main__':
    with Connection(redis_connection):
        queues = map(Queue, sys.argv[1:]) or [Queue()]
        worker = Worker(queues)
        worker.push_exc_handler(retry_handler)
        from osf_scraper_api.web.app import create_app
        app = create_app()
        with app.app_context():
            worker.work()
