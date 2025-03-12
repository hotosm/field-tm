#!/bin/bash

set -eo pipefail

wait_for_db() {
    max_retries=30
    retry_interval=5

    for ((i = 0; i < max_retries; i++)); do
        if </dev/tcp/"${FMTM_DB_HOST:-fmtm-db}"/5432; then
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
        http_status=$(curl --silent --head --write-out "%{http_code}" --output /dev/null "${S3_ENDPOINT}/${S3_BUCKET_NAME}")

        # We allow 400 or 403, as the service is available but likely blocked by proxy
        if [[ "$http_status" == "200" || "$http_status" == "403" || "$http_status" == "400" ]]; then
            echo "S3 is available (HTTP $http_status)."
            return 0  # S3 is available, exit successfully
        fi

        echo "S3 is not yet available (HTTP $http_status). Retrying in ${retry_interval} seconds..."
        sleep ${retry_interval}
    done

    echo "Timed out waiting for S3 to become available."
    exit 1  # Exit with an error code
}

create_s3_buckets() {
    echo "Running init_s3_buckets.py script main function"
    python /opt/app/s3.py
}

# Start wait in background with tmp log files
wait_for_db &
wait_for_s3 &
# Wait until checks complete
wait

# Skip init S3 if env var present
if [ "${S3_SKIP_BUCKET_INIT}" != true ]; then
    create_s3_buckets
fi

exec "$@"
