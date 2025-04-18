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

check_fmtm_db_vars_present() {
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

check_central_db_vars_present() {
    if [ -z "${CENTRAL_DB_HOST}" ]; then
        echo "Environment variable CENTRAL_DB_HOST is not set."
        exit 1
    fi
    if [ -z "${CENTRAL_DB_USER}" ]; then
        echo "Environment variable CENTRAL_DB_USER is not set."
        exit 1
    fi
    if [ -z "${CENTRAL_DB_PASSWORD}" ]; then
        echo "Environment variable CENTRAL_DB_PASSWORD is not set."
        exit 1
    fi
    if [ -z "${CENTRAL_DB_NAME}" ]; then
        echo "Environment variable CENTRAL_DB_NAME is not set."
        exit 1
    fi
}

wait_for_db() {
    local db_host="$1"
    local max_retries=30
    local retry_interval=5

    for ((i = 0; i < max_retries; i++)); do
        if </dev/tcp/"${db_host}"/5432; then
            echo "Database is available."
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

backup_db() {
    local db_host="$1"
    local db_user="$2"
    local db_name="$3"
    local db_password="$4"
    local db_backup_file
    db_backup_file="$HOME/${db_name}_$(date +'%Y%m%d%H%M%S').dump"

    echo "Running VACUUM ANALYZE on the database."
    PGPASSWORD="$db_password" psql --host "$db_host" \
        --username "$db_user" "$db_name" -c "VACUUM ANALYZE;"

    echo "Dumping current database to backup file: $db_backup_file"
    PGPASSWORD="$db_password" pg_dump --verbose --encoding utf8 \
        --format c --file "${db_backup_file}" \
        --host "$db_host" --username "$db_user" "$db_name" \
        >> /dev/null 2>&1

    echo "gzipping file --> ${db_backup_file}.gz"
    gzip "$db_backup_file"
    db_backup_file="${db_backup_file}.gz"

    BUCKET_NAME="fmtm-db-backups"
    echo "Uploading to S3 bucket ${BUCKET_NAME}"
    mc alias set s3 "$S3_ENDPOINT" "$S3_ACCESS_KEY" "$S3_SECRET_KEY"
    mc mb "s3/${BUCKET_NAME}" --ignore-existing
    mc anonymous set download "s3/${BUCKET_NAME}"
    mc cp "${db_backup_file}" "s3/${BUCKET_NAME}/${db_name}/"
}
### Functions END ###



####################
### Script START ###
####################

echo "Waiting 5 minutes (for migrations) before first backup."
sleep 600

while true; do
    ### FMTM Backup ###
    pretty_echo "### Backup FMTM $(date +%Y-%m-%d_%H:%M:%S) ###"
    check_fmtm_db_vars_present
    wait_for_db "${FMTM_DB_HOST:-fmtm-db}"
    wait_for_s3
    backup_db "${FMTM_DB_HOST:-fmtm-db}" "${FMTM_DB_USER:-fmtm}" \
        "${FMTM_DB_NAME:-fmtm}" "${FMTM_DB_PASSWORD}"
    pretty_echo "### Backup FMTM Complete ###"

    ### ODK Backup ###
    # Only run ODK Central DB Backups if the database is included in the stack
    # Exec is used to wrap the error messages / suppress output
    if (exec 3>/dev/tcp/"${CENTRAL_DB_HOST}"/5432) 2>/dev/null; then
        pretty_echo "### Backup ODK Central $(date +%Y-%m-%d_%H:%M:%S) ###"
        check_central_db_vars_present
        # wait_for_db "${CENTRAL_DB_HOST:-central-db}"
        backup_db "${CENTRAL_DB_HOST:-central-db}" "${CENTRAL_DB_USER:-odk}" \
            "${CENTRAL_DB_NAME:-odk}" "${CENTRAL_DB_PASSWORD}"
        pretty_echo "### Backup ODK Central Complete ###"
    else
        echo "Skipping ODK DB Backup (instance is remote)."
    fi

    echo "Waiting 24hrs until next backup."
    sleep 86400
done

####################
###  Script END  ###
####################
