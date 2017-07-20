"""
Adapted from https://github.com/ui/rq-scheduler/blob/9a1891e135bb8b8f5ef2bd03e8063e1d2bec7296/rq_scheduler/scripts/rqscheduler.py
"""
from redis import StrictRedis
from rq_scheduler import Scheduler
from rq_scheduler.utils import setup_loghandlers

from hello_settings import ENV_DICT


def main():
    redis_connection = StrictRedis(
        host=ENV_DICT.get('REDIS_HOST', 'localhost'),
        port=ENV_DICT.get('REDIS_PORT', 6379),
        db=ENV_DICT.get('REDIS_DB', 0),
        password=ENV_DICT.get('REDIS_PASSWORD')
    )
    interval = ENV_DICT.get('RQ_SCHEDULER_POLLING_INTERVAL', 60)
    verbose = ENV_DICT.get('RQ_SCHEDULER_VERBOSE_OUTPUT', False)
    burst = ENV_DICT.get('RQ_SCHEDULER_BURST_MODE', False)

    if verbose:
        log_level = 'DEBUG'
    else:
        log_level = 'INFO'
    setup_loghandlers(log_level)

    scheduler = Scheduler(connection=redis_connection, interval=interval)
    scheduler.run(burst=burst)


if __name__ == '__main__':
    main()
