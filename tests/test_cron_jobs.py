from unittest.mock import patch

import pytest

from app.clients.pub_sub import create_message
from app.models.cron_jobs import consumer, producer


class TestCronJobs:
    @pytest.mark.skip
    @patch('app.models.cron_jobs.verify_token', return_value=None)
    def test_alerts_notify(self, verify_token_mock, app_client, dummy_token):
        response = app_client.post(
            url=f"/v1/test/cronjob/",
            json={},
            headers={
                "Authorization": f"Bearer {dummy_token}"
            }
        )
        assert response.status_code == 200

    @pytest.mark.skip
    def test_producer(self, pubsub_data):
        # response = create_message(data_list=pubsub_data)
        response = producer(test=True)
        assert response is True

    @pytest.mark.skip
    def test_consumer(self):
        response = consumer(test=True)
        assert response is True
