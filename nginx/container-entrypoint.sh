#!/bin/bash

set -eo pipefail

echo
echo "Substituing env vars"
echo
bash /docker-entrypoint.d/20-envsubst-on-templates.sh

echo
echo "Starting NGINX in the background"
echo
nginx -g "daemon off;" > /dev/null 2>&1 &

# Wait for NGINX to start with a maximum timeout of 20 seconds
timeout=20
while [ $timeout -gt 0 ]; do
    if nc -z localhost 80; then
        break
    fi

    echo ""
    echo "Waiting for NGINX to be running..."
    sleep 2
    timeout=$((timeout - 2))
done

# Check if the timeout was reached
if [ $timeout -eq 0 ]; then
  echo "NGINX did not start within the timeout."
  exit 1
fi

# Check if FMTM_DOMAIN is set
if [ -z "${FMTM_DOMAIN}" ]; then
    echo "${FMTM_DOMAIN} variable is not set. Exiting."
    exit 1
fi

# Check if FMTM_API_DOMAIN is set
if [ -z "${FMTM_API_DOMAIN}" ]; then
    echo "${FMTM_API_DOMAIN} variable is not set. Exiting."
    exit 1
fi

# Renew certs arg (default api & frontend only)
certbot_args=(
    "--webroot" "--webroot-path=/var/www/certbot" \
    "--email" "${CERT_EMAIL}" "--agree-tos" "--no-eff-email" \
    "-d" "${FMTM_DOMAIN}" "-d" "${FMTM_API_DOMAIN}" \
)

# Add FMTM_ODK_DOMAIN if present
if [ -n "${FMTM_ODK_DOMAIN}" ]; then
    echo "Adding ${FMTM_ODK_DOMAIN} to certificate for domain ${FMTM_DOMAIN}."
    certbot_args+=("-d" "${FMTM_ODK_DOMAIN}")
fi

# Add FMTM_S3_DOMAIN if present
if [ -n "${FMTM_S3_DOMAIN}" ]; then
    echo "Adding ${FMTM_S3_DOMAIN} to certificate for domain ${FMTM_DOMAIN}."
    certbot_args+=("-d" "${FMTM_S3_DOMAIN}")
fi

# Run certbot with the constructed arguments
echo "Running command: certbot --non-interactive certonly ${certbot_args[@]}"
certbot --non-interactive certonly "${certbot_args[@]}"
echo "Certificate generated under: /etc/letsencrypt/live/${FMTM_DOMAIN}/"

# Add FMTM_SCRIPT_DOMAIN if present
if [ -n "${FMTM_SCRIPT_DOMAIN}" ] && [ "${FMTM_SCRIPT_DOMAIN}" != "_" ]; then
    echo
    echo "FMTM_SCRIPT_DOMAIN variable set. Generating separate certificate."
    certbot --non-interactive certonly \
        --webroot --webroot-path=/var/www/certbot \
        --email "${CERT_EMAIL}" --agree-tos --no-eff-email \
        -d "${FMTM_SCRIPT_DOMAIN}"
fi

# Successful exit (stop container)
exit 0
