import datetime

from osf_scraper_api.utilities.rq_helper import get_redis_connection, get_running_rq_jobs

from redis import Redis
from rq import Queue
from rq import Worker

def rq_stats():
    rcon = get_redis_connection()
    qfail = Queue("failed", connection=rcon)
    print qfail.count

    for qname in ['osf0', 'osf1']:
        q = Queue(qname, connection=rcon)
        print '{}: {}'.format(qname, q.count)

        running = get_running_rq_jobs(queue_name=qname)
        for job in running:
            print job.id


def rq_clear_failed():
    rcon = get_redis_connection()
    qfail = Queue("failed", connection=rcon)
    print qfail.count
    qfail.empty()
    print qfail.count


def rq_remove_zombies():
    workers_and_tasks = []
    connection = get_redis_connection()
    workers = Worker.all(connection=connection)
    for worker in workers:
        job = worker.get_current_job()
        if job is not None:
            job.ended_at = datetime.datetime.utcnow()
            worker.failed_queue.quarantine(job, exc_info=("Dead worker", "Moving job to failed queue"))
        worker.register_death()


if __name__ == '__main__':
    rq_stats()
    # rq_clear_failed()
    # rq_remove_zombies()