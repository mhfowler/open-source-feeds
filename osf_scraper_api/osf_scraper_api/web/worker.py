"""
Adapted from https://gist.github.com/spjwebster/6521272
"""
import sys
import os
import datetime

from redis import StrictRedis
from rq_scheduler import Scheduler
from rq import Worker, Queue, Connection, get_failed_queue

from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.utilities.log_helper import _capture_rq_exception, _log
from osf_scraper_api.utilities.rq_helper import get_running_rq_jobs, get_osf_queue, restart_failed_jobs

redis_connection = StrictRedis(
    host=ENV_DICT.get('REDIS_HOST'),
    port=ENV_DICT.get('REDIS_PORT'),
    db=ENV_DICT.get('REDIS_DB'),
    password=ENV_DICT.get('REDIS_PASSWORD')
)
default_max_failures = ENV_DICT.get('RQ_DEFAULT_MAX_JOB_FAILURES', 2)
default_retry_delay = ENV_DICT.get('RQ_DEFAULT_RETRY_DELAY', 120)

queues = None


def retry_handler(job, exc_type, exc_value, traceback):
    # try to log the exception
    try:
        _capture_rq_exception(exc_type=exc_type, exc_value=exc_value, exc_traceback=traceback)
    except:
        pass

    # # retries
    # job.refresh()
    # failures = job.meta.get('failures', 0) + 1
    # max_failures = job.meta.get('max_failures', default_max_failures)
    #
    # if failures >= max_failures:
    #     _log('rq job %s: failed too many times times - moving to failed queue' % job.id)
    #     return True
    #
    # _log('rq job %s: failed %d times - retrying' % (job.id, failures))
    #
    # # there is a closure over queues so that we can specify them as command line arguments
    # for queue in queues:
    #     if queue.name == job.origin:
    #         # use rq_scheduler to delay scheduling the job
    #         retry_delay = job.meta.get('retry_delay', default_retry_delay)
    #         scheduler = Scheduler(connection=redis_connection, queue_name=job.origin)
    #         job = scheduler.enqueue_in(
    #             datetime.timedelta(seconds=retry_delay),
    #             job.func,
    #             *job.args,
    #             **job.kwargs
    #         )
    #         job.meta['failures'] = failures
    #         job.save()
    #         return False

    # and then regardless, return True, such that exception gets passed
    # to the next handler which puts it in the failed queue
    return True


if __name__ == '__main__':
    with Connection(redis_connection):
        queue_names = sys.argv[1:]
        queues = map(Queue, queue_names) or [Queue()]
        _log('++ listening to queues: {}'.format(queue_names))
        worker = Worker(queues)
        worker.push_exc_handler(retry_handler)

        requeue_queue = get_osf_queue(queue_names[0])

        if ENV_DICT.get('CLEAR_OLD_RQ_WORKERS'):
            workers = Worker.all()
            _log('++ clearing any inactive workers')
            if not workers:
                _log('++ no workers found')
            else:
                for w in workers:
                    if w.state != 'busy':
                        _log('++ stopping rq worker {}'.format(w.pid))
                        job = w.get_current_job()
                        if job is not None:
                            _log('++ requeing zombie job {}'.format(job.id))
                            job.ended_at = datetime.datetime.utcnow()
                            requeue_queue.enqueue_job(job)
                        w.register_death()

            # clear all running jobs
            for queue_name in queue_names:
                running_jobs = get_running_rq_jobs(queue_name)
                for job in running_jobs:
                    _log('++ requeue running job {}'.format(job.id))
                    job.ended_at = datetime.datetime.utcnow()
                    requeue_queue.enqueue_job(job)

        # restart failed jobs
        if ENV_DICT.get('RESTART_FAILED_JOBS'):
            restart_failed_jobs()

        from osf_scraper_api.web.app import create_app
        app = create_app()
        with app.app_context():
            worker.work()
