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
from osf_scraper_api.utilities.fs_helper import file_exists, save_dict, load_dict

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
    #     _log('++ rq job {} {}: failed {} times - moving to failed queue'.format(job.func_name, job.id, str(failures)))
    #     return True
    #
    # _log('++ immediately retrying job {} {}: failed {} times - retrying'.format(job.func_name, job.id, str(failures)))
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

        worker_num = os.environ.get('RQ_PROCESS_NUM')
        if worker_num:
            _log('++ worker_num: {}'.format(worker_num))
            worker_id_path = 'workers/{}'.format(worker_num)
            requeue_queue = get_osf_queue(queue_names[0])
            # try to remove zombie worker
            if file_exists(worker_id_path):
                old_worker_dict = load_dict(worker_id_path)
                old_worker_name = old_worker_dict['worker_name']
                workers = Worker.all()
                for w in workers:
                    if w.name == old_worker_name:
                        _log('++ removing zombie worker: {}'.format(old_worker_name))
                        job = w.get_current_job()
                        if job is not None:
                            _log('++ requeing job {}'.format(job.id))
                            job.ended_at = datetime.datetime.utcnow()
                            requeue_queue.enqueue_job(job)
                        w.register_death()
            # save name of current worker
            worker_dict = {'worker_name': worker.name}
            save_dict(worker_dict, worker_id_path)

        from osf_scraper_api.web.app import create_app
        app = create_app()
        with app.app_context():
            worker.work()
