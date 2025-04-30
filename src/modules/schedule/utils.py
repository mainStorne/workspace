from datetime import datetime, timedelta

from crontab import CronTab


def crontab_range(start: datetime, stop: datetime, cron: CronTab):
    while True:
        start = cron.next(now=start, return_datetime=True, default_utc=True)
        reminder = start.minute % 15
        if reminder != 0 or start.minute == 0:
            start += timedelta(minutes=15 - reminder)
        if start > stop:
            break
        if start == stop:
            yield start
            break
        if start.hour < 8 or start.hour > 22:
            continue
        if start.hour == 22 and start.minute != 0:
            continue
        yield start
