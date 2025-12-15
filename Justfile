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

mod start 'tasks/start'
mod stop 'tasks/stop'
mod build 'tasks/build'
mod test 'tasks/test'
mod config 'tasks/config'
mod manage 'tasks/manage'
mod prep 'tasks/prep'

# List available commands
[private]
default:
  just help

# List available commands
help:
  just --justfile {{justfile()}} --list

# Delete local database, S3, and ODK Central data
clean:
  docker compose down -v

# Run pre-commit hooks
lint:
  #!/usr/bin/env sh
  cd {{justfile_directory()}}/src/backend
  uv run pre-commit run --all-files

# Increment field-tm
bump:
  #!/usr/bin/env sh
  cd {{justfile_directory()}}/src/backend
  uv run cz bump --check-consistency

# Increment osm-fieldwork (doesn't work yet!)
bump-osm-fieldwork:
  #!/usr/bin/env sh
  cd {{justfile_directory()}}/src/backend
  uv --project packages/osm-fieldwork --directory packages/osm-fieldwork run cz bump --check-consistency

# Run docs website locally
docs:
  #!/usr/bin/env sh
  cd {{justfile_directory()}}/src/backend
  uv sync --group docs
  uv run mkdocs serve --config-file ../../mkdocs.yml --dev-addr 0.0.0.0:3000

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
