"""
app.py
"""

import logging
from logging.handlers import RotatingFileHandler
# from logging.config import dictConfig
from typing import Tuple

import flask
from flask import Flask, request, make_response, jsonify
from flask_restful import Api
from flask_cors import CORS

import nltk
from transformers import AutoTokenizer, AutoModel
from pymorphy2 import MorphAnalyzer
from stop_words import get_stop_words
import string

from src.models import Model
from src.exceptions import InvalidUsage
from src.response_templates import response_success


# Load BERT model
BERT = Model()

MORPHER = MorphAnalyzer()
STOP_WORDS = set(get_stop_words("ru") + nltk.corpus.stopwords.words('russian'))
EXCLUDE = set(string.punctuation)


def answer() -> flask.make_response:
    """answer endpoint

    Returns
    -------
    flask.make_response
        JSON response
    """

    if not request.is_json or len(request.json) == 0:
        raise InvalidUsage.bad_request()

    question = preprocess_question(request.json['question'])
    answer = get_answer(question)

    res = make_response(jsonify(response_success(
        answer=answer,
        status_code=200,
    )))
    return res

def preprocess_question(question: str) -> str:
    """Preprocess question for BERT model

    Parameters
    ----------
    question : str
        Question text

    Returns
    -------
    str
        Preprocessed question
    """

    spls = "".join(i for i in question.strip() if i not in EXCLUDE).split()
    spls = [MORPHER.parse(i.lower())[0].normal_form for i in spls]
    spls = [i for i in spls if i not in STOP_WORDS and i != ""]
    return ' '.join(spls)

def get_answer(question: str) -> str:
    """Get answer from BERT model

    Parameters
    ----------
    question : str
        Question

    Returns
    -------
    str
        Answer text
    """

    try:
        question = preprocess_question(question)
        tok = tokenizer(question, padding=True, truncation=True, max_length=24, return_tensors='pt')
        vector = BERT(**tok)[1].detach().numpy()[0]
        return index.get_nns_by_vector(vector, 2)
    except TypeError as error:
        raise InvalidUsage.bad_request() from error

def create_app() -> Flask:
    """Create flask app

    Returns
    -------
    Flask
        Flask app
    """

    app = Flask(__name__)
    CORS(app, resources={r"*": {"origins": "*"}})
    Api(app)
    app.add_url_rule('/answer', view_func=answer, methods=['POST'])

    register_errorshandler(app)
    register_logger(app)
    return app

def register_errorshandler(app: Flask) -> None:
    """Regitering errors handler

    Parameters
    ----------
    app : Flask
        Flask app
    """

    def errorhandler(error):
        """Error handler

        Parameters
        ----------
        error : str
            Error

        Returns
        -------
        str
            Error in JSON format
        """

        response = error.to_json()
        response.status_code = error.status_code
        return response

    app.errorhandler(InvalidUsage)(errorhandler)

def register_logger(app: Flask) -> None:
    """Regitering logger

    Parameters
    ----------
    app : Flask
        Flask app
    """

    handler = RotatingFileHandler(
        filename='app.log',
        maxBytes=100000,
        backupCount=10
    )
    handler.setLevel(logging.ERROR)
    app.logger.addHandler(handler)
