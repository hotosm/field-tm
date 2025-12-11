# Copyright (c) Humanitarian OpenStreetMap Team
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#

# NOTE this dockerfile simply extends the official image
# to init an admin user at startup

ARG ODK_CENTRAL_TAG


FROM ghcr.io/getodk/central-service:${ODK_CENTRAL_TAG}
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "ca-certificates" \
        "jq" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

COPY container-entrypoint.sh /
RUN chmod +x /container-entrypoint.sh
ENTRYPOINT ["/container-entrypoint.sh"]
