import logging
from datetime import datetime
from functools import partial
import pytz
from http.client import OK

from fastapi import APIRouter, Depends
from google.cloud import firestore_v1

from app import config
from app.auth import oauth2_scheme, verify_token
from app.clients.bigquery import BigQueryClient
from app.clients.pub_sub import create_message, get_messages
from app.utils import query
from app.utils.http import get_int_code_by_http_codename

utc = pytz.UTC
router = APIRouter()
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)
client = firestore_v1.Client()

bigquery_client = BigQueryClient()


def parse_data(data_query: str) -> dict:
    parsed_data = {}
    for row in bigquery_client.execute_query(query=data_query):
        row = dict(row)
        if 'total' in row:
            parsed_data['total'] = row['total']
        else:
            parsed_data['total'] = 0

    total = parsed_data.get('total') if parsed_data.get('total') else 0
    return total


def get_parsed_data(table, billing_account_id, start_date, end_date):
    query_preparer = partial(
        query.prepare_query,
        project_id=config.PROJECT_ID,
        dataset=config.DATASET,
        table=table,
        billing_account_id=billing_account_id,
        start_date=start_date,
        end_date=end_date,
    )

    data_parsed_query = query_preparer(query=query.get_service_data_by_customer())

    parsed_data = parse_data(data_query=data_parsed_query)

    return parsed_data


def get_service_alerts(customer_id: str, start_date):
    logger.info('Getting alerts to be triggered')
    service_alerts = [
        {x.id: x.to_dict()} for x in
        client.collection("alerts").document(customer_id).collection('rules').where('enable', '==', True).where(
            'group_by', '==', 'service').where('triggered', '==', None).get()]
    service_alerts_triggered = [
        {x.id: x.to_dict()} for x in
        client.collection("alerts").document(customer_id).collection('rules').where('enable', '==', True).where(
            'group_by', '==', 'service').where('triggered', '<', start_date).get()]
    if service_alerts_triggered:
        for alert in service_alerts_triggered:
            service_alerts.append(alert)

    return service_alerts


def get_cron_dates():
    today = utc.localize(datetime.today())
    start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = today.month

    return {
        'start_date': start_date,
        'end_date': today,
        'this_month': this_month
    }


def consumer(test: bool = False):
    get_messages(test)
    return True


def producer(test: bool = False):
    logger.warning('init')
    dates = get_cron_dates()
    table = config.BQ_PRE_AGGREGATED_BY_PROJECT
    logger.info(dates)
    logger.info(table)
    customers = client.collection("alerts").get()
    logger.warning(customers)
    pub_sub_values = []

    for customer in customers:
        logger.info(f'START processing customer {customer.id}')
        # check alerts to process
        service_alerts = get_service_alerts(customer_id=customer.id, start_date=dates.get('start_date'))

        if service_alerts:
            # Get billing_account_id
            try:
                logger.info('Getting customer alert document')
                customer_dict = client.collection("customers").document(customer.id).get().to_dict()
                billing_account_id = customer_dict.get("billing_account_id")
            except Exception as err:
                logger.error(err)
                continue

            # Query services total
            customer_total = get_parsed_data(table=table, billing_account_id=billing_account_id,
                                             start_date=dates.get('start_date').date(),
                                             end_date=dates.get('end_date').date())

            if service_alerts and customer_total > 0:
                for record in service_alerts:
                    key = [k for k, v in record.items()][0]
                    if record[key].get('quota', 0) > 0 and record[key].get('quota') < customer_total:
                        logger.info('Creating message to send to pubsub')
                        data_dict = {
                            'customer_id': customer.id,
                            'customer_name': customer_dict.get('customer_name'),
                            'billing_account_id': billing_account_id,
                            'service_total': customer_total,
                            'alert': {
                                'alert_id': key,
                                'created_date': str(record[key].get('created_date')),
                                'group_by': record[key].get('group_by'),
                                'quota': record[key].get('quota'),
                                'enable': record[key].get('enable'),
                                'triggered': record[key].get('triggered'),
                            },
                            'users': customer_dict.get('alert'),
                            'test': test
                        }
                        pub_sub_values.append(data_dict)

                if pub_sub_values:
                    logger.info('creating messages')
                    create_message(data_list=pub_sub_values)
                    logger.info('messages created and sent to pubsub')

    return True


@router.post(
    path='/v1/test/cronjob/',
    tags=['v1/test/cronjob'],
    status_code=get_int_code_by_http_codename(OK)
)
def alerts_notify(token: str = Depends(oauth2_scheme)):
    verify_token(token)
    producer(test=True)
    consumer(test=True)
