FROM python:3.7.7
LABEL "repository"="https://github.com/albul-k/jokesbot"
LABEL "maintainer"="Konstantin Albul"

EXPOSE 5000

# Set the working directory to /app
WORKDIR /usr/src/app

# Copy files
COPY setup.sh .
COPY docker-entrypoint.sh .
COPY requirments.txt .
COPY run_app.py .
COPY src/ src/
COPY common/ common/

# Install the dependencies
RUN ["sh", "./setup.sh"]

# Entrypoint
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]