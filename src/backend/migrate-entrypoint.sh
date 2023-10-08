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
}

wait_for_db() {
    max_retries=30
    retry_interval=5

    for ((i = 0; i < max_retries; i++)); do
        if </dev/tcp/${FMTM_DB_HOST:-fmtm-db}/5432; then
            echo "Database is available."
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
        psql "$db_url" -f "/opt/migrations/init/fmtm_base_schema.sql"
        pretty_echo "Schema created successfully."
        return 0
    fi
}

create_migrations_table_if_missing() {
    echo "Creating _migrations table if not exists."
    psql "$db_url" <<SQL
    DO \$\$
    BEGIN
        CREATE TABLE public."_migrations" (
            script_name TEXT,
            date_executed TIMESTAMP,
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

    # Iterate through files under /opt/migrations
    for script_file in /opt/migrations/*.sql; do
        # Extract the script name from the file path
        script_name=$(basename "$script_file")

        # Check if the script_name is in the list of existing scripts
        if ! echo "$existing_scripts" | grep -q "$script_name"; then
            echo "Migration script '$script_name' needs to be executed. Adding to list."
            scripts_to_execute+=("$script_name")
        fi
    done
}

backup_db() {
    echo "Backing up database, prior to migrations."
    db_backup_file="$HOME/fmtm_pre_migrate_$(date +'%Y%m%d%H%M%S').dump"

    echo "Running VACUUM ANALYZE on the database."
    PGPASSWORD="$FMTM_DB_PASSWORD" psql --host "$FMTM_DB_HOST" \
        --username "$FMTM_DB_USER" "$FMTM_DB_NAME" -c "VACUUM ANALYZE;"

    pretty_echo "Dumping current database to backup file."
    PGPASSWORD="$FMTM_DB_PASSWORD" pg_dump --verbose --format c \
        --file "${db_backup_file}" \
        --host "$FMTM_DB_HOST" --username "$FMTM_DB_USER" "$FMTM_DB_NAME"

    gzip "$db_backup_file"
    pretty_echo "Backup complete: $db_backup_file.gz"
}

execute_migrations() {
    for script_name in "${scripts_to_execute[@]}"; do
        script_file="/opt/migrations/$script_name"
        pretty_echo "Executing migration: $script_name"
        psql "$db_url" -a -f "$script_file"

        # Add an entry in the migrations table to indicate completion
        psql "$db_url" <<SQL
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

create_svc_user() {
    pretty_echo "Creating default svcfmtm user."
    psql "$db_url" <<SQL
    DO \$\$
    BEGIN
        INSERT INTO users (id, username, role, mapping_level, tasks_mapped, tasks_validated, tasks_invalidated)
        VALUES (20386219, 'svcfmtm', 'MAPPER', 'BEGINNER', 0, 0, 0);
        RAISE NOTICE 'User "svcfmtm" (uid 20386219) successfully created.';
    EXCEPTION   
        WHEN OTHERS THEN
            RAISE NOTICE 'User "svcfmtm" (uid 20386219) already exists.';
    END\$\$;
SQL
}
### Functions END ###



####################
### Script START ###
####################

pretty_echo "### Script Start ###"

# Var: array of migration files to run
scripts_to_execute=()

# DB startup
check_all_db_vars_present
wait_for_db
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
pretty_echo "Migrations complete."

# Create service user account, if not exists
create_svc_user

pretty_echo "### Script End ###"

####################
###  Script END  ###
####################

exec "$@"
