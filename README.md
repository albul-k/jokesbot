# JokesBot

[![docker-ci](https://github.com/albul-k/jokesbot/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/albul-k/jokesbot/actions/workflows/main.yml)

## Table of contents

* [Description](#description)
* [Used stack](#used-stack)
* [Work algorithm](#work-algorithm)
* [How to run](#how-to-run)
* [REST API](#rest-api)

## Description

Do you like jokes? JokesBot knows over 100k jokes =)

Just give him a theme or keyword.

>_Note: `JokesBot` knows only russian jokes._


## Used stack

* ML: FastText, sklearn, annoy, pymorphy2, stop_words
* Web: Flask
* [Jokes database](https://github.com/albul-k/scraper_jokes)

## Work algorithm

First of all, the entered text goes through preprocessing - cleaning from stop words, punctuation, morphological analysis.

Then it is transformed into a vector and the search for the most similar vector in the pretrained FastText model is performed for it.

If the distance between the vectors is less than or equal to the threshold of 0.25, then the text of the joke corresponding to the found vector is displayed.

If the threshold is exceeded, then the preprocessed text enters the LinearSVC model to predict the theme of the joke. Next, we randomly extract one joke on the predicted topic.

### Link to [EDA](https://github.com/albul-k/jokesbot/blob/main/eda/eda.ipynb)

## How to run

### Pull the Docker image from Docker Hub and run it

```bash
docker pull albulk/jokesbot:latest
docker run -d -p 5000:5000 albulk/jokesbot
```

### Open [http://localhost:5000/](http://localhost:5000/)

## REST API

### Link to [API](https://github.com/albul-k/jokesbot/blob/main/openapi.yml)

### Example

```bash
curl --location --request POST 'http://localhost:5000/joke' \
--header 'Content-Type: application/json' \
--data-raw '{
    "text": "чукча"
}'
```
