import logging
from datetime import datetime
from http.client import OK

import google
import pytz
from fastapi import APIRouter, Depends, HTTPException
from google.cloud import firestore_v1

from app import config
from app.auth import oauth2_scheme, verify_token
from app.models.models import AlertInputModel, PayloadAlertsResponseModel
from app.utils.http import get_int_code_by_http_codename

utc = pytz.UTC
router = APIRouter()
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)
client = firestore_v1.Client()


@router.get(
    path='/v1/alerts/{customer_id}/',
    tags=['v1/alerts'],
    status_code=get_int_code_by_http_codename(OK),
    response_model=PayloadAlertsResponseModel
)
def list_alerts(customer_id, token: str = Depends(oauth2_scheme)):
    verify_token(token)
    if customer_id is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    alerts_dict = {x.id: x.to_dict() for x in
                   client.collection("alerts").document(customer_id).collection('rules').get()}
    response = {"payload": []}
    data_dict = {}

    for key, values in alerts_dict.items():
        try:
            if values.get("group_by") not in data_dict:
                data_dict[values.get("group_by")] = {
                    key: values.get("quota"),
                }
            else:
                data_dict[values.get("group_by")].update({
                    key: values.get("quota"),
                })
        except Exception as err:
            logger.error(err)
            continue

    response["payload"].append(data_dict)
    return response


def create_alert_method(customer_id: str, alert_id: str, values: dict, group_by: str, token_info: dict):
    try:
        client.collection("alerts").document(customer_id).set({}, merge=True)
        customer_alerts = client.collection("alerts").document(customer_id).collection('rules')
        alert_dict = {
            "group_by": group_by.lower(),
            "quota": int(values[alert_id]),
            "triggered": None,
            "enable": True,
            "created_by": token_info.get('email') if token_info else '',
            "created_date": datetime.now()
        }

        customer_alerts.document(alert_id).set(alert_dict, merge=True)

    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=400, detail="The data sent is not correct!")


def update_alert_method(customer_id: str, alert_id: str, update_data: dict):
    try:
        alert = client.collection("alerts").document(customer_id).collection('rules').document(alert_id)
        alert.update(update_data)
    except google.api_core.exceptions.NotFound:
        raise HTTPException(status_code=404, detail="Alert not found!")

    return alert


@router.post(
    path="/v1/alerts/{customer_id}/",
    tags=["v1/alerts"],
    status_code=get_int_code_by_http_codename(OK),
    response_model=PayloadAlertsResponseModel
)
def set_alert(customer_id, alert_data: AlertInputModel, token: str = Depends(oauth2_scheme)):
    token_info = verify_token(token)
    if customer_id is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    for key, values in alert_data.dict().items():
        for record in values:
            alert = client.collection("alerts").document(customer_id).collection('rules').document(record).get()
            if not alert.exists:
                create_alert_method(customer_id=customer_id, alert_id=record, values=values, group_by=key,
                                    token_info=token_info)
            else:
                if alert.to_dict().get('quota') != int(values[record]):
                    update_data = {
                        'quota': int(values[record]),
                        'triggered': None
                    }
                    update_alert_method(customer_id=customer_id, alert_id=record, update_data=update_data)

    response = list_alerts(customer_id=customer_id, token=token)
    return response


def create_log(data: dict, message: str):
    data.update({'message': message})

    if data.get('customer_id'):
        customer_logs = client.collection("alerts").document(data.get('customer_id')).collection('logs')

        new_log = customer_logs.document()
        new_log.set(data, merge=True)
    else:
        raise HTTPException(status_code=404, detail="Customer not found!")

    return True


def check_alert(message_data: dict):
    try:
        today = utc.localize(datetime.today())
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        customer_id = message_data.get('customer_id')
        alert_id = message_data.get('alert').get('alert_id')
        alert = client.collection("alerts").document(customer_id).collection('rules').document(alert_id).get().to_dict()
        if alert.get('triggered') and alert.get('triggered') >= start_date:
            logger.info('message not sent because it was already triggered')
            return False
    except HTTPException as err:
        create_log(data=message_data, message=err.detail)
        logger.error(err, exc_info=err)
        return False

    return True
