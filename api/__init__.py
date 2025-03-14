from fastapi import FastAPI

from .modules import schedule

app = FastAPI()
app.include_router(schedule.r)
