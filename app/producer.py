import logging

from app import config
from app.models.cron_jobs import producer

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('Starting Producer')
    producer()
    logger.info('Finished Producer')
