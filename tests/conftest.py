from datetime import datetime

import pytest
from google.cloud import firestore_v1
from starlette.testclient import TestClient

from app.main import app

client = firestore_v1.Client()

DUMMY_TOKEN = "12345678"
TEST_CUSTOMER_ID = "CWl1C1rddDNyh0YBgML6"
TEST_NEW_ALERT = {
    'service': {
        'quota1': 2000,
        'quota2': 5000,
        'quota3': 8000
    },
    'resource_labels': {
        'label1': {
            'quota1': '',
            'quota2': '',
            'quota3': '',
        },
        'bananas': {
            'quota1': '',
            'quota2': '',
            'quota3': '',
        },
    },
}
TEST_UPDATE_ALERT = {
    'service': {
        'quota1': 3000,
        'quota2': 5000,
        'quota3': 8000
    },
}


@pytest.fixture
def app_client():
    return TestClient(app=app)


@pytest.fixture
def dummy_token():
    return DUMMY_TOKEN


@pytest.fixture
def customer_id():
    return TEST_CUSTOMER_ID


@pytest.fixture
def new_alert():
    return TEST_NEW_ALERT


@pytest.fixture
def update_alert():
    return TEST_UPDATE_ALERT


@pytest.fixture
def pubsub_data():
    return [{
        'customer_id': 'CWl1C1rddDNyh0YBgML6',
        'billing_account_id': '01899B-6918AE-A75D35',
        'total': 5955.321599999957,
        'alert': {
            'alert_id': 'quota1',
            'created_date': str(datetime.now()),
            'group_by': 'service',
            'quota': 5000.0,
            'enable': True,
            'triggered': None,
        },
        'users': 'emanuel.ferreira@devoteam.com',
        'test': True
    }]
