"""
app.py
"""

import logging
from logging.handlers import RotatingFileHandler

import string
import pickle
import sqlite3 as sql
from flask import Flask, request, make_response, jsonify, render_template, flash, redirect, \
                  url_for, g
import flask
from flask_restful import Api
from flask_cors import CORS

from gensim.models import FastText
from annoy import AnnoyIndex
from pymorphy2 import MorphAnalyzer
from stop_words import get_stop_words
import numpy as np

from src.exceptions import InvalidUsage
from src.response_templates import response_success


DB_PATH = 'train/jokes.db'

# FastText indexes
F_VECT = 30
FT_INDEX = AnnoyIndex(F_VECT, 'angular')
FT_INDEX.load('train/ft_index.ann')

# FastText model
MODEL_FT = FastText.load('train/model_FT.ft')

# Indexed jokes
with open('train/index_map.pkl', 'rb') as file:
    INDEX_MAP = pickle.load(file)

# Encoder with joke themes
with open('train/label_encoder.pkl', 'rb') as file:
    LABEL_ENCODER = pickle.load(file)

# LinearSVC model
with open('train/model_svc.pkl', 'rb') as file:
    MODEL_SVC = pickle.load(file)

# TfidfVectorizer
with open('train/tfidf.pkl', 'rb') as file:
    TFIDF = pickle.load(file)
IDFS = {v[0]: v[1] for v in zip(TFIDF.vocabulary_, TFIDF.idf_)}
MIDF = np.mean(TFIDF.idf_)

MORPHER = MorphAnalyzer()
STOP_WORDS = set(get_stop_words("ru"))
EXCLUDE = set(string.punctuation)


def get_db() -> sql.connect:
    """Get connect to SQL database

    Returns
    -------
    sql.connect
        Connection object
    """

    db_conn = getattr(g, '_database', None)
    if db_conn is None:
        db_conn = g._database = sql.connect(DB_PATH)
    return db_conn

def close_connection(exception) -> None:
    """Close DB connect

    Parameters
    ----------
    exception : [type]
        [description]
    """

    db_conn = getattr(g, '_database', None)
    if db_conn is not None:
        db_conn.close()

def home() -> flask.render_template:
    """Start url

    Returns
    -------
    flask.render_template
        flask.render_template string
    """

    return render_template('home.html')

def handle_joke_form() -> flask.redirect:
    """Handle joke theme form

    Returns
    -------
    flask.redirect
        flask.redirect response
    """

    text = request.form['text']
    if text:
        try:
            joke_ = get_joke(text)
            flash(joke_, 'alert-success')
        except InvalidUsage as error:
            flash('<br/>'.join(error.message['errors']), 'alert-danger')
    else:
        flash('You have not asked the subject of the joke', 'alert-warning')
    return redirect(url_for("home"))

def joke() -> str:
    """Endpoint joke

    Returns
    -------
    str
        html

    Raises
    ------
    InvalidUsage.bad_request
        Raises 404 if request JSON is wrong
    """

    if not request.is_json or len(request.json) == 0:
        raise InvalidUsage.bad_request()

    joke_ = get_joke(request.json['text'])

    res = make_response(jsonify(response_success(
        text=joke_,
        status_code=200,
    )))
    return res

def preprocess_text(text: str) -> str:
    """Preprocess text

    Parameters
    ----------
    text : str
        text

    Returns
    -------
    str
        Preprocessed text
    """

    spls = "".join(i for i in text.strip() if i not in EXCLUDE).split()
    spls = [MORPHER.parse(i.lower())[0].normal_form for i in spls]
    spls = [i for i in spls if i not in STOP_WORDS and i != ""]
    return ' '.join(spls)

def get_joke(text: str) -> str:
    """Get joke

    Parameters
    ----------
    text : str
        text

    Returns
    -------
    str
        Joke text
    """

    def embed_txt(text: str, idfs: dict, midf: float) -> np.ndarray:
        """Make embedding from text string

        Parameters
        ----------
        text : str
            text
        idfs : dict
            TFIDF map
        midf : float
            Mean idf

        Returns
        -------
        np.ndarray
            Embedding
        """

        n_ft = 0
        vector_ft = np.zeros(F_VECT)
        for word in text:
            if word in MODEL_FT.wv:
                vector_ft += MODEL_FT.wv[word] * idfs.get(word, midf)
            n_ft += idfs.get(word, midf)
        return vector_ft / n_ft

    def query_db(query: str, one: bool = True) -> tuple:
        """Query to DB

        Parameters
        ----------
        query : str
            Query text
        one : bool, optional
            Return one row if True, by default True

        Returns
        -------
        tuple
            Query result
        """

        cur = get_db().execute(query)
        rows = cur.fetchall()
        cur.close()
        return (rows[0] if rows else None) if one else rows

    try:
        text = preprocess_text(text)
        text_ = TFIDF.transform([text])

        vect_ft = embed_txt(text, IDFS, MIDF)
        ft_index_val, distances = FT_INDEX.get_nns_by_vector(vect_ft, 1, include_distances=True)
        joke_ = None
        for item, dist in zip(ft_index_val, distances):
            if dist <= 0.25:
                joke_ = INDEX_MAP[item][1]
            break
        if joke_:
            return joke_

        theme = MODEL_SVC.predict(text_)
        theme = LABEL_ENCODER.inverse_transform(theme)[0]
        sql_query = f'SELECT text FROM joke WHERE theme == "{theme}" ORDER BY RANDOM() LIMIT 1'
        joke_ = query_db(sql_query, one=True)
        return joke_[0]
    except Exception as error:
        raise InvalidUsage.unknown_error() from error

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
    app.config['SECRET_KEY'] = 'mysecretkey'
    app.add_url_rule('/', view_func=home, methods=['GET'])
    app.add_url_rule('/joke', view_func=joke, methods=['POST'])
    app.add_url_rule('/handle_joke_form', view_func=handle_joke_form, methods=['POST'])
    app.teardown_appcontext(close_connection)

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
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)
