def get_int_code_by_http_codename(code_object: int) -> int:
    """
    Converts http.HTTPStatus code into a int code
    """
    assert code_object
    return int(code_object)
