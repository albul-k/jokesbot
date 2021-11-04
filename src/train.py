import string
import pickle
import sqlite3 as sql

import os
from gensim.models import FastText
from annoy import AnnoyIndex
from pymorphy2 import MorphAnalyzer
from stop_words import get_stop_words
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer


class MyIter:

    def __init__(self, data: pd.DataFrame) -> None:
        self.data = data

    def __iter__(self):
        for _, row in self.data.iterrows():
            yield row['text_token']


def main():
    def preprocess_txt(line):
        spls = "".join(i for i in line.strip() if i not in exclude).split()
        spls = [morpher.parse(i.lower())[0].normal_form for i in spls]
        spls = [i for i in spls if i not in sw and i != ""]
        return ' '.join(spls)

    morpher = MorphAnalyzer()
    sw = set(get_stop_words("ru"))
    exclude = set(string.punctuation)

    cur = sql.connect('train/jokes.db').execute('SELECT theme,text FROM joke')
    rows = cur.fetchall()
    cur.close()

    jokes = {idx: {'theme': itm[0], 'text': itm[1]} for idx,itm in enumerate(rows)}

    df = pd.DataFrame.from_dict(jokes, columns=['theme', 'text'], orient='index')
    df['text_token'] = df['text'].apply(lambda x: preprocess_txt(x))

    le = LabelEncoder()
    df['theme'] = le.fit_transform(df['theme'])

    with open(os.path.join('train', 'label_encoder.pkl'), 'wb') as file:
        pickle.dump(le, file)

    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=10000
    )

    svc = LinearSVC(
        random_state=100,
        max_iter=1000,
        loss='squared_hinge',
        dual=False,
    )
    svc.fit(tfidf.fit_transform(df['text_token']), df['theme'])

    with open(os.path.join('train', 'model_svc.pkl'), 'wb') as file:
        pickle.dump(svc, file)

    modelFT = FastText(sentences=MyIter(df), size=30, min_count=1, window=5, workers=8)
    modelFT.save(os.path.join('train', 'model_FT.ft'))

    ft_index = AnnoyIndex(30 ,'angular')

    idfs = {v[0]: v[1] for v in zip(tfidf.vocabulary_, tfidf.idf_)}
    midf = np.mean(tfidf.idf_)

    index_map = {}
    counter = 0

    for index, row in df.iterrows():
        n_ft = 0
        index_map[counter] = (df.loc[index, "theme"], df.loc[index, "text"], df.loc[index, "text_token"])
        vector_ft = np.zeros(30)
        for word in df.loc[index, "text_token"]:
            if word in modelFT.wv:
                vector_ft += modelFT.wv[word] * idfs.get(word, midf)
                n_ft += idfs.get(word, midf)
        if n_ft > 0:
            vector_ft = vector_ft / n_ft
        ft_index.add_item(counter, vector_ft)
        counter += 1

    ft_index.build(10)
    ft_index.save(os.path.join('train', 'ft_index.ann'))

    with open(os.path.join('train', 'index_map.pkl'), 'wb') as file:
        pickle.dump(index_map, file)

    with open(os.path.join('train', 'tfidf.pkl'), 'wb') as file:
        pickle.dump(tfidf, file)
