# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
# 

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
