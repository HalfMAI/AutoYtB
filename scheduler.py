from pytz import utc
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
from utitls import myLogger

g_main_scheduler = None
def __init__():
    global g_main_scheduler
    g_main_scheduler = BackgroundScheduler(timezone=utc)
    g_main_scheduler.add_jobstore('sqlalchemy', url='sqlite:///jobs.sqlite')
    g_main_scheduler.start()

    log_jobs()

    import threading
    myLogger("g_main_scheduler in this thread:{}".format(threading.current_thread()))


def add_date_job(datetime_str, job_id, task, args_):
    global g_main_scheduler
    run_time = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    run_time = run_time - timedelta(minutes=30)

    try:
        g_main_scheduler.add_job(task, args=args_, id=job_id, name=task.__qualname__, next_run_time=run_time, misfire_grace_time=3600*2)
    except ConflictingIdError:
        g_main_scheduler.modify_job(job_id, func=task, args=args_, name=task.__qualname__, next_run_time=run_time)
    log_jobs()


def log_jobs():
    global g_main_scheduler
    for v in g_main_scheduler.get_jobs():
        myLogger("jobId:{}, jobName:{}, jobNextTime{}".format(v.id, v.name, v.next_run_time))


def get_jobs():
    global g_main_scheduler
    return g_main_scheduler.get_jobs()

# init the scheduler
__init__()
