from unittest.mock import patch

import pytest


class TestAlerts:
    @pytest.mark.skip
    @patch('app.models.alerts.verify_token', return_value=None)
    def test_set_alert(self, verify_token_mock, app_client, customer_id, new_alert, dummy_token):
        """ Test for listing an alert """
        response = app_client.post(
            url=f"/v1/alerts/{customer_id}/",
            json=new_alert,
            headers={
                "Authorization": f"Bearer {dummy_token}"
            }
        )
        content = response.json()
        assert response.status_code == 200

    @pytest.mark.skip
    @patch('app.models.alerts.verify_token', return_value=None)
    def test_update_alert(self, verify_token_mock, app_client, customer_id, update_alert, dummy_token):
        """ Test for listing an alert """
        response = app_client.post(
            url=f"/v1/alerts/{customer_id}/",
            json=update_alert,
            headers={
                "Authorization": f"Bearer {dummy_token}"
            }
        )
        content = response.json()
        assert response.status_code == 200

    @pytest.mark.skip
    @patch('app.models.alerts.verify_token', return_value=None)
    def test_list_alerts(self, verify_token_mock, app_client, customer_id, dummy_token):
        """ Test for listing all alerts for one customer """
        response = app_client.get(
            url=f"/v1/alerts/{customer_id}/",
            headers={
                "Authorization": f"Bearer {dummy_token}"
            }
        )
        content = response.json()
        assert response.status_code == 200
