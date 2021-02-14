import os
import time
from datetime import datetime

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from vaccine_finder.jobs import riteaid_job

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
JOB_INTERVAL = int(os.environ.get('JOB_INTERVAL', 30))


def schedule_jobs():
    """
    Schedule vaccine finding jobs. Then start counter to inform time 
    until next job
    """
    conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
    scheduler = Scheduler(connection=conn)
    queue = Queue(connection=conn)

    # Cancel/delete jobs from queue and registries before scheduling
    print('Canceling any existing jobs ...')
    for job_id in ['riteaid_finder']:
        for job in scheduler.get_jobs():
            print(f'Cancel job {job.id}')
            job.cancel()
    queue.delete(delete_jobs=True)

    # RiteAid Job
    scheduler.schedule(
        id='riteaid_finder',
        scheduled_time=datetime.now(),
        func=riteaid_job,
        interval=JOB_INTERVAL,
        repeat=None,
    )


def counter():
    """
    Count down until next job is queued
    """
    time_delta = 5
    t = 0
    while True:
        print(f'Time until next job queues: {JOB_INTERVAL - t} seconds')
        time.sleep(time_delta)
        t += time_delta
        if t >= JOB_INTERVAL:
            t = 0
            print('Queueing job now ...')


if __name__ == '__main__':
    print('Scheduling jobs ...')
    schedule_jobs()
    counter()