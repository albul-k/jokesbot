"""
response_templates.py
"""

from typing import List


def response_success(text: str,
                     status_code: int = 200) -> dict:
    """Template for success response

    Parameters
    ----------
    text : str
        text
    status_code : int, optional
        Status code of response, by default 200

    Returns
    -------
    dict
        Dictionary with template
    """

    templ = {
        'message': {
            'text': text,
        },
        'status_code': status_code
    }
    return templ

def response_error(data: List[str], status_code: int = 500) -> dict:
    """Template for error response

    Parameters
    ----------
    data : List[str]
        List of strings with error text
    status_code : int, optional
        Status code of response, by default 500

    Returns
    -------
    dict
        Dictionary with template
    """

    templ = {
        'message': {
            'errors': data
        },
        'status_code': status_code
    }
    return templ
