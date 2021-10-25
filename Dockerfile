FROM python:3.7.7
LABEL "repository"="https://github.com/albul-k/nn_chatbot_backend"
LABEL "maintainer"="Konstantin Albul"

EXPOSE 5000

# Set the working directory to /app
WORKDIR /usr/src/app

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install the dependencies
ADD requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/

# run the command to start uWSGI
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run_app:APP"]