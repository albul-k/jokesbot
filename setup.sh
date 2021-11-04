#!/bin/bash

# install venv
pip install virtualenv
virtualenv venv
source venv/bin/activate

# install dependencies
pip install -r ./requirments.txt