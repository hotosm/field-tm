FROM ghcr.io/opengisch/qfieldcloud-qgis:25.24
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1
RUN pip install --no-warn-script-location --break-system-packages \
      --no-cache-dir qgis-plugin-manager==1.7.2 \
    && cd /usr/share/qgis/python/plugins/ \
    && qgis-plugin-manager init \
    && qgis-plugin-manager update \
    && qgis-plugin-manager install "XLSForm Converter" \
    && echo 'hasProcessingProvider=yes' >> /usr/share/qgis/python/plugins/xlsformconverter/metadata.txt
COPY project_gen_svc.py /usr/src/app/
CMD ["python3", "/usr/src/app/project_gen_svc.py"]
