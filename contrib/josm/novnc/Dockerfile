#checkov:skip=CKV_DOCKER_7: Only tag available in registry
FROM docker.io/theasp/novnc:latest
COPY index.html /usr/share/novnc/
RUN useradd -r -u 900 -m -c "novnc account" -d /home/appuser -s /bin/false appuser \
    && chown -R appuser:appuser /app
WORKDIR /app
USER appuser
