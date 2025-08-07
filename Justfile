# Copyright (c) Humanitarian OpenStreetMap Team
#
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

set dotenv-load

mod start 'contrib/just/start/Justfile'
mod stop 'contrib/just/stop/Justfile'
mod build 'contrib/just/build/Justfile'
mod test 'contrib/just/test/Justfile'
mod config 'contrib/just/config/Justfile'
mod stats 'contrib/just/stats/Justfile'
mod manage 'contrib/just/manage/Justfile'
mod prep 'contrib/just/prep/Justfile'

# List available commands
[private]
default:
  just help

# List available commands
help:
  just --justfile {{justfile()}} --list

# Run database migrations for backend
migrate:
  docker compose up -d migrations

# Delete local database, S3, and ODK Central data
clean:
  docker compose down -v

# Run pre-commit hooks
lint:
  TAG_OVERRIDE=ci TARGET_OVERRIDE=ci docker compose run --rm --no-deps \
    --volume $PWD:$PWD --workdir $PWD \
    --entrypoint='sh -c' api \
    'git config --global --add safe.directory $PWD \
    && pre-commit run --all-files'

# Increment version
bump:
  TAG_OVERRIDE=ci TARGET_OVERRIDE=ci docker compose run --rm --no-deps \
    --volume $PWD:$PWD --workdir $PWD \
    --entrypoint='sh -c' api \
    'git config --global --add safe.directory $PWD \
    && git config --global user.name svcfmtm \
    && git config --global user.email fmtm@hotosm.org \
    && cd src/backend \
    && cz bump --check-consistency --no-verify'

# Run docs website locally
docs:
  @echo
  @echo "\033[0;33m ############################################### \033[0m"
  @echo
  @echo
  @echo "\033[0;34m Access the docs site on: http://localhost:55425 \033[0m"
  @echo
  @echo
  @echo "\033[0;33m ############################################### \033[0m"
  @echo

  TAG_OVERRIDE=ci TARGET_OVERRIDE=ci docker compose run --rm --no-deps \
    --volume $PWD:$PWD --workdir $PWD --publish 55425:3000 \
    --entrypoint='sh -c' api \
    'git config --global --add safe.directory $PWD \
    && mkdocs serve --dev-addr 0.0.0.0:3000'

# Mount an S3 bucket on your filesystem
mount-s3:
  #!/usr/bin/env sh
  set -e

  fstab_entry="fmtm-data /mnt/fmtm/local fuse.s3fs _netdev,allow_other,\
  use_path_request_style,passwd_file=/home/$(whoami)/s3-creds/fmtm-local,\
  url=http://s3.fmtm.localhost:7050 0 0"

  if ! grep -q "$fstab_entry" /etc/fstab; then
      echo "Mounting local Field-TM S3 permanently in /etc/fstab"
      echo "$fstab_entry" | sudo tee -a /etc/fstab > /dev/null
      echo
  else
      echo "Local Field-TM S3 is already mounted"
  fi

# Echo to terminal with blue colour
[no-cd]
_echo-blue text:
  #!/usr/bin/env sh
  printf "\033[0;34m%s\033[0m\n" "{{ text }}"

# Echo to terminal with yellow colour
[no-cd]
_echo-yellow text:
  #!/usr/bin/env sh
  printf "\033[0;33m%s\033[0m\n" "{{ text }}"

# Echo to terminal with red colour
[no-cd]
_echo-red text:
  #!/usr/bin/env sh
  printf "\033[0;41m%s\033[0m\n" "{{ text }}"
