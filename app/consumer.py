import logging

from app import config
from app.models.cron_jobs import consumer

logging.basicConfig(level=config.LOG_LEVEL)

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logger.info('Starting Consumer')
    consumer()
    logger.info('Finished Consumer')
