FROM ubuntu:14.04

# different builds for different environment
ARG BUILD_ENV
RUN echo "++ building Dockerfile for env: ${BUILD_ENV}"

# constants
ENV APP_NAME osf_scraper_api
ENV REPO_URL git@github.com:mhfowler/open-source-feeds.git
ENV REPO_REMOTE origin
ENV SRC_DIR /srv/app
ENV SRV_DIR /srv
ENV LOG_DIR /srv/log
ENV PUBLIC_DIR /srv/public
ENV ENV_PATH "devops/secret_files/env/${BUILD_ENV}"

# Update OS
RUN apt-get update
RUN apt-get -y upgrade

# Install Python
RUN apt-get install -y python-dev python-pip

# Install other dependencies
RUN apt-get install -y \
    libpq-dev \
    nginx \
    curl

# copy over nginx conf
COPY devops/build/nginx.conf /etc/nginx/nginx.conf
COPY devops/build/nginx_site.conf /etc/nginx/sites-available/app.conf
RUN rm /etc/nginx/sites-enabled/*
RUN ln -s \
    /etc/nginx/sites-available/app.conf \
    /etc/nginx/sites-enabled/app.conf

# create user groups
RUN groupadd webgroup
RUN usermod -G webgroup root
RUN useradd -G webgroup ubuntu
RUN useradd -G webgroup nginx-user
RUN useradd -G webgroup uwsgi-user

# copy over ssh keys
COPY devops/secret_files/osf_rsa.pub /root/.ssh/id_rsa.pub
COPY devops/secret_files/osf_rsa /root/.ssh/id_rsa

# ensure directories
RUN mkdir $LOG_DIR

# copy code
COPY . $SRC_DIR

# install python requirements
RUN pip install -r "${SRC_DIR}/osf_scraper_api/requirements.txt"

# copy hellow_webapp.ini
COPY devops/build/app.ini "${SRC_DIR}/app.ini"

# Install Supervisord
RUN apt-get update && apt-get install -y supervisor \
&& rm -rf /var/lib/apt/lists/*
# Custom Supervisord config
COPY devops/templates/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# copy env.json
RUN echo "++ env_path: "$ENV_PATH
RUN rm "${SRC_DIR}/osf_scraper_api/env.json"
COPY $ENV_PATH "${SRC_DIR}/env.json"

# set file permissions
RUN chgrp -R webgroup /srv
RUN chmod -R u=rwX,g=rwX,o=X /srv

# Expose ports for nginx
EXPOSE 80 443

# start app
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]