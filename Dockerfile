# pull the official docker image
FROM python:3.9.5-slim

# set work directory
WORKDIR /code

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install postgresql package requirements
RUN apt update && \
    apt install -y libpq-dev gcc

# install frontend dependencies
COPY src/web/requirements.txt /code/frontend_requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/frontend_requirements.txt

# install backend dependencies
COPY src/backend/requirements.txt /code/backend_requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/backend_requirements.txt

# copy project
# COPY . .
COPY . /code
