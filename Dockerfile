FROM python:3.7.7
LABEL "repository"="https://github.com/albul-k/jokesbot"
LABEL "maintainer"="Konstantin Albul"

EXPOSE 5000

# Set the working directory to /app
WORKDIR /usr/src/app

RUN python -m pip install --upgrade pip

COPY requirments.txt .
RUN pip install -r ./requirments.txt

# Copy files
COPY run_app.py .
COPY src/ src/
COPY train/ train/

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run_app:APP"]