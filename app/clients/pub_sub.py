import json
import logging
from datetime import datetime

from fastapi import HTTPException
from google.cloud import pubsub_v1
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Mail

from app import config
from app.models.alerts import check_alert, create_log, update_alert_method

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


def create_message(data_list: list):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(config.PROJECT_ID, config.BILLING_ALERTS_TOPIC_ID)
    logger.info(f'topic {topic_path} detected')
    for data in data_list:
        data_json = json.dumps(data, indent=4, default=str)
        logger.info(f'data parsed {data_json}')
        publish_future = publisher.publish(topic_path, data_json.encode("utf-8"))
        logger.info(f'publish result {str(publish_future)}')
        publish_future.result()
        create_log(data=data, message='Message created on Pub/Sub')
        logger.info('message sent to pubsub')

    return True


def job_send_email(message_data):
    to_emails = message_data.get('users')
    if not to_emails:
        raise HTTPException(status_code=404, detail="Users to send alert to not found.")

    internal_message = False
    external_message = False
    internal_to_emails = list(filter(lambda x: '@devoteam.com' in x, to_emails))
    external_to_emails = list(filter(lambda x: '@devoteam.com' not in x, to_emails))

    template_payload = {
        "domain": config.CC_WEBSITE,
        "target": message_data.get('alert').get('quota'),
        "customer_name": message_data.get('customer_name')
    }
    if message_data.get('test'):
        template_payload.update({'test_env_msg': 'This is a test email!'})
    group_by = message_data.get('alert').get('group_by')
    if group_by == 'service':
        template_payload.update({'service': True})

    if internal_to_emails:
        internal_from_mail = Email(email='gcp-developers@avalonsolutions.com', name='CommandCenter')
        internal_message = Mail(from_email=internal_from_mail, to_emails=internal_to_emails)
        internal_message.dynamic_template_data = template_payload
        internal_message.template_id = config.BILLING_ALERT_TEMPLATE_ID

    if external_to_emails:
        external_from_mail = Email(email='noreply@devoteamcloud.com', name='CommandCenter')
        external_message = Mail(from_email=external_from_mail, to_emails=external_to_emails)
        external_message.dynamic_template_data = template_payload
        external_message.template_id = config.BILLING_ALERT_TEMPLATE_ID

    try:
        sg = SendGridAPIClient(config.SENDGRID_API_KEY)
        if internal_message:
            sg.send(internal_message)
        if external_message:
            sg.send(external_message)
        logger.info('email sent')
    except Exception as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail=f"There was an issue sending email via SendGrid. ({err})")


def get_messages(test):
    def callback(message: pubsub_v1.subscriber.message.Message, test: bool) -> bool:
        message_data = json.loads(message.message.data)
        send_mail = check_alert(message_data=message_data)
        if message_data.get('test') == test and send_mail:
            datetime_now = datetime.now()
            message_data['alert'].update({'triggered': datetime_now})
            create_log(data=message_data, message=f"Message pulled from Pub/Sub.")
            try:
                update_alert_method(
                    customer_id=message_data.get('customer_id'),
                    alert_id=message_data.get('alert').get('alert_id'),
                    update_data={'triggered': message_data.get('alert').get('triggered')})
                job_send_email(message_data=message_data)
                create_log(data=message_data, message="Email sent.")
            except HTTPException as err:
                create_log(data=message_data, message=err.detail)
                logger.error(err, exc_info=err)
                return True

        return True

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(config.PROJECT_ID, config.BILLING_ALERTS_SUBSCRIPTION_ID)

    logger.info(f'subscription path {subscription_path} detected')

    while True:
        response = subscriber.pull(request={'subscription': subscription_path, 'max_messages': config.MAX_MESSAGES})
        logger.info('response received')

        if not response.received_messages:
            logger.info("No more received messages")
            break

        acknowledge_ids = []
        acknowledge_data = []

        for message in response.received_messages:
            logger.info(f'messages received: {message}')
            if callback(message=message, test=test):
                logger.info('callback successful processed ')
                acknowledge_ids.append(message.ack_id)
                acknowledge_data.append(json.loads(message.message.data))

        if acknowledge_ids:
            subscriber.acknowledge(request={'subscription': subscription_path, 'ack_ids': acknowledge_ids})
            for data in acknowledge_data:
                create_log(data=data, message="Pub/Sub Messages Acknowledged.")
            logger.info('messages acknowledged')
