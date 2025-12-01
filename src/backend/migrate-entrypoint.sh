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

check_all_s3_vars_present() {
    if [ -z "${S3_ENDPOINT}" ]; then
        echo "Environment variable S3_ENDPOINT is not set."
        exit 1
    fi
    if [ -z "${S3_ACCESS_KEY}" ]; then
        echo "Environment variable S3_ACCESS_KEY is not set."
        exit 1
    fi
    if [ -z "${S3_SECRET_KEY}" ]; then
        echo "Environment variable S3_SECRET_KEY is not set."
        exit 1
    fi
    if [ -z "${S3_BUCKET_NAME}" ]; then
        echo "Environment variable S3_BUCKET_NAME is not set."
        exit 1
    fi
    if [ -z "${S3_BACKUP_BUCKET_NAME}" ]; then
        echo "Environment variable S3_BACKUP_BUCKET_NAME is not set."
        exit 1
    fi

    # Strip any extra unrequired "quotes"
    export S3_ENDPOINT="${S3_ENDPOINT//\"/}"
    export S3_ACCESS_KEY="${S3_ACCESS_KEY//\"/}"
    export S3_SECRET_KEY="${S3_SECRET_KEY//\"/}"
    export S3_BUCKET_NAME="${S3_BUCKET_NAME//\"/}"
    export S3_BACKUP_BUCKET_NAME="${S3_BACKUP_BUCKET_NAME//\"/}"
    export S3_QFIELD_BUCKET_NAME="${S3_QFIELD_BUCKET_NAME//\"/}"
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

wait_for_s3() {
    max_retries=10
    retry_interval=5

    # First wait a few seconds for Minio
    sleep 5
    echo "Testing S3 connection to ${S3_ENDPOINT}"
    for ((i = 0; i < max_retries; i++)); do
        http_status=$(curl --silent --head --write-out "%{http_code}" --output /dev/null "${S3_ENDPOINT}/minio/health/live")

        if [[ "$http_status" == "200" ]]; then
            echo "S3 is available (HTTP $http_status)."
            return 0  # S3 is available, exit successfully
        fi

        echo "S3 is not yet available (HTTP $http_status). Retrying in ${retry_interval} seconds..."
        sleep ${retry_interval}
    done

    echo "Timed out waiting for S3 to become available."
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

init_buckets() {
    BACKUP_BUCKET_NAME=${S3_BACKUP_BUCKET_NAME}
    QFIELD_BUCKET_NAME=${S3_QFIELD_BUCKET_NAME}
    echo "Ensuring S3 bucket ${BUCKET_NAME} exists"
    mc alias set s3 "${S3_ENDPOINT}" "${S3_ACCESS_KEY}" "${S3_SECRET_KEY}"

    mc mb "s3/${S3_BUCKET_NAME}" --ignore-existing
    mc anonymous set download "s3/${S3_BUCKET_NAME}"

    mc mb "s3/${BACKUP_BUCKET_NAME}" --ignore-existing
    mc anonymous set download "s3/${BACKUP_BUCKET_NAME}"

    if [ -n "${QFIELD_BUCKET_NAME}" ]; then
        mc mb "s3/${QFIELD_BUCKET_NAME}" --ignore-existing
        mc anonymous set download "s3/${QFIELD_BUCKET_NAME}"
    fi
}

backup_db() {
    echo "Backing up database, prior to migrations."
    db_backup_file="$HOME/fmtm_pre_migrate_$(date +'%Y%m%d%H%M%S').dump"

    echo "Running VACUUM ANALYZE on the database."
    PGPASSWORD="$FMTM_DB_PASSWORD" psql --host "$FMTM_DB_HOST" \
        --username "$FMTM_DB_USER" "$FMTM_DB_NAME" -c "VACUUM ANALYZE;"

    pretty_echo "Dumping current database to backup file: $db_backup_file"
    PGPASSWORD="$FMTM_DB_PASSWORD" pg_dump --verbose --encoding utf8 \
        --format c --file "${db_backup_file}" \
        --host "$FMTM_DB_HOST" --username "$FMTM_DB_USER" "$FMTM_DB_NAME"

    echo "gzipping file --> ${db_backup_file}.gz"
    gzip --force "$db_backup_file"
    db_backup_file="${db_backup_file}.gz"

    BUCKET_NAME=${S3_BACKUP_BUCKET_NAME}
    echo "Uploading to S3 bucket ${BUCKET_NAME}"
    mc cp "${db_backup_file}" "s3/${BUCKET_NAME}/pre-migrate/"

    pretty_echo "Backup complete: $db_backup_file to bucket ${BUCKET_NAME}/pre-migrate/"
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
check_all_s3_vars_present; echo "✓ S3 vars check complete"
wait_for_db
wait_for_s3
init_buckets
db_url="postgresql://${FMTM_DB_USER}:${FMTM_DB_PASSWORD}@${FMTM_DB_HOST}/${FMTM_DB_NAME}"

# Apply schema, if needed
create_db_schema_if_missing
create_migrations_table_if_missing

# Run migrations, if needed
check_if_missing_migrations
if [ ${#scripts_to_execute[@]} -gt 0 ]; then
    backup_db
    execute_migrations
else
    pretty_echo "No new migrations found."
fi
pretty_echo "### Migrations End ###"

####################
###  Script END  ###
####################
