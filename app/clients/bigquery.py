from typing import Any

from google.cloud import bigquery


class BigQueryClient:
    """
    BigQuery wrapper
    """
    client = bigquery.Client()

    def execute_query(self, query: str, **kwargs) -> Any:
        """
        Runs BQ query
        Args:
            query (str): query to be handled by BQ

        Returns:
            a new instance of job query
        """
        assert query
        return self.client.query(query=query, **kwargs)
