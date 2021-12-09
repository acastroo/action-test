def prepare_query(
        query: str,
        **kwargs
) -> str:
    """
    BQ query preparer.
    Prepares a given query to be executed in BQ
    """
    return query.format(
        project_id=kwargs.get('project_id'),
        dataset=kwargs.get('dataset'),
        table=kwargs.get('table'),
        billing_account_id=kwargs.get('billing_account_id'),
        start_date=kwargs.get('start_date'),
        end_date=kwargs.get('end_date')
    )


def get_service_data_by_customer() -> str:
    return """
        SELECT
            sum(amount) AS total
        FROM
            `{project_id}.{dataset}.{table}`
        WHERE 
            this_date BETWEEN '{start_date}' AND '{end_date}'
            AND billing_account_id = '{billing_account_id}'
        GROUP BY billing_account_id
    """
