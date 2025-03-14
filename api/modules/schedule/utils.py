from datetime import datetime

from crontab import CronTab


def crontab_range(start: datetime, stop: datetime, cron: CronTab):
    while True:
        step = cron.next(now=start, return_datetime=True, default_utc=True)
        start = step
        if start > stop:
            break
        yield step
