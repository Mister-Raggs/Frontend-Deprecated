FROM python:3.11.4-slim-bullseye

WORKDIR /usr/src/app

# copy the requirements file into the image
COPY . .

ENV DEBIAN_FRONTEND=noninteractive
ENV APP_ENV=local-docker

# install the dependencies and packages in the requirements file
# Install native libraries, required for numpy
RUN rm -rf ./.venv                                                              &&\
    rm -rfv ./flask-session-store/*                                             &&\
    rm -rfv ./logs/*                                                            &&\
    apt-get update                                                              &&\
    apt-get install -y apt-utils bash curl wget vim libmagic1                   &&\
    pip3 install --root-user-action=ignore --upgrade --no-cache-dir pip         &&\
    pip3 install --root-user-action=ignore --no-cache-dir -r requirements.txt   &&\
    apt-get clean                                                               &&\
    rm -rfv /var/lib/apt/lists/*

EXPOSE 8080

# configure the container to run in an executed manner
ENTRYPOINT [ "gunicorn", "--config", "gunicorn.conf.py", "-e", "env=${APP_ENV}", "run:app" ]
