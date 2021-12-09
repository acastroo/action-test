import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from app import config
from .models.alerts import router as alerts_router
from .models.cron_jobs import router as cron_jobs_router

app = FastAPI(docs_url="/alerts/docs", openapi_url="/alerts/openapi.json")

origins = os.environ.get('ORIGINS', []).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=30,
)

routers = [
    alerts_router,
    cron_jobs_router
]

for router in routers:
    app.include_router(router)


@app.get('/alerts', status_code=status.HTTP_200_OK)
async def healthcheck():
    return {}


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8001, debug=config.DEBUG, log_level=config.LOG_LEVEL.lower())
