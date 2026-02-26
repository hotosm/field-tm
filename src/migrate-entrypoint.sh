#!/bin/bash

set -eo pipefail

### Functions START ###

pretty_echo() {
    local message="$1"
    local length=${#message}
    local separator=""

    for ((i=0; i<length+4; i++)); do
        separator="$separator-"
    done

    echo ""
    echo "$separator"
    echo "$message"
    echo "$separator"
    echo ""
}

check_all_db_vars_present() {
    if [ -z "${FMTM_DB_HOST}" ]; then
        echo "Environment variable FMTM_DB_HOST is not set."
        exit 1
    fi
    if [ -z "${FMTM_DB_USER}" ]; then
        echo "Environment variable FMTM_DB_USER is not set."
        exit 1
    fi
    if [ -z "${FMTM_DB_PASSWORD}" ]; then
        echo "Environment variable FMTM_DB_PASSWORD is not set."
        exit 1
    fi
    if [ -z "${FMTM_DB_NAME}" ]; then
        echo "Environment variable FMTM_DB_NAME is not set."
        exit 1
    fi

    # Strip any extra unrequired "quotes"
    export FMTM_DB_HOST="${FMTM_DB_HOST//\"/}"
    export FMTM_DB_USER="${FMTM_DB_USER//\"/}"
    export FMTM_DB_PASSWORD="${FMTM_DB_PASSWORD//\"/}"
    export FMTM_DB_NAME="${FMTM_DB_NAME//\"/}"
}

wait_for_db() {
    max_retries=30
    retry_interval=5

    for ((i = 0; i < max_retries; i++)); do
        if </dev/tcp/"${FMTM_DB_HOST:-fmtm-db}"/5432; then
            echo "✓ Database is available."
            return 0  # Database is available, exit successfully
        fi
        echo "Database is not yet available. Retrying in ${retry_interval} seconds..."
        sleep ${retry_interval}
    done

    echo "Timed out waiting for the database to become available."
    exit 1  # Exit with an error code
}

create_db_schema_if_missing() {
    table_exists=$(psql -t "$db_url" -c "
        SELECT EXISTS (SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'projects');
    " | tr -d '[:space:]')  # Remove all whitespace and formatting characters
    echo "Debug: return from table_exists query: $table_exists"

    if [ "$table_exists" = "t" ]; then
        echo "Data exists in the database. Skipping schema creation."
        return 0
    else
        echo "No data found in the database."
        pretty_echo "Creating schema."
        # We must cd into the dir for relative modular script imports
        cd /opt/migrations/init
        psql "$db_url" -f "./0-main.sql"
        pretty_echo "Schema created successfully."
        cd /opt
        return 0
    fi
}

create_migrations_table_if_missing() {
    echo "Creating _migrations table if not exists."
    psql "$db_url" <<SQL
    DO \$\$
    BEGIN
        CREATE TABLE public."_migrations" (
            script_name text,
            date_executed timestamp without time zone,
            CONSTRAINT "_migrations_pkey" PRIMARY KEY (script_name)
        );
        ALTER TABLE IF EXISTS public."_migrations" OWNER TO fmtm;
        RAISE NOTICE 'Table "_migrations" successfully added to database.';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Table "migrations" already exists. Skipping...';    
    END\$\$;
SQL
}

check_if_missing_migrations() {
    # Get the list of existing migration script names from the migrations table
    existing_scripts=$(psql -t "$db_url" -c "
        SELECT script_name FROM public.\"_migrations\" ORDER BY date_executed ASC;
    ")
    echo "Existing migrations: ${existing_scripts}"

    # Check if there are .sql files under /opt/migrations and iterate
    migration_files=$(find /opt/migrations -maxdepth 1 -type f -name '*.sql')
    if [ -z "$migration_files" ]; then
        echo "No migration scripts found in /opt/migrations directory."
        return
    fi

    # Iterate through migration files
    for script_file in $migration_files; do
        # Extract the script name from the file path
        script_name=$(basename "$script_file")

        # Check if the script_name is in the list of existing scripts
        if ! echo "$existing_scripts" | grep -q "$script_name"; then
            echo "Migration script '$script_name' needs to be executed. Adding to list."
            scripts_to_execute+=("$script_name")
        fi
    done
}

execute_migrations() {
    mapfile -t ordered_scripts < <(for script in "${scripts_to_execute[@]}"; do echo "$script"; done | sort)

    for script_name in "${ordered_scripts[@]}"; do
        script_file="/opt/migrations/$script_name"
        pretty_echo "Executing migration: $script_name"
        # Apply migration with env vars substituted & if succeeds,
        # add an entry in the migrations table to indicate completion
        envsubst < "$script_file" | psql "$db_url" \
            --set ON_ERROR_STOP=1 --echo-all \
        && psql "$db_url" <<SQL
    DO \$\$
    BEGIN
        INSERT INTO public."_migrations" (date_executed, script_name)
        VALUES (NOW(), '$script_name');
        RAISE NOTICE 'Successfully applied migration: $script_name';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Failed to add migration to database: $script_name';
    END\$\$;
SQL
    done
}

### Functions END ###



####################
### Script START ###
####################

pretty_echo "### Migrations Start ###"

# Var: array of migration files to run
scripts_to_execute=()

# DB startup
check_all_db_vars_present; echo "✓ DB vars check complete"
wait_for_db
db_url="postgresql://${FMTM_DB_USER}:${FMTM_DB_PASSWORD}@${FMTM_DB_HOST}/${FMTM_DB_NAME}"

# Apply schema, if needed
create_db_schema_if_missing
create_migrations_table_if_missing

# Run migrations, if needed
check_if_missing_migrations
if [ ${#scripts_to_execute[@]} -gt 0 ]; then
    execute_migrations
else
    pretty_echo "No new migrations found."
fi
pretty_echo "### Migrations End ###"

####################
###  Script END  ###
####################
