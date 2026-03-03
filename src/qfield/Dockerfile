FROM ghcr.io/opengisch/qfieldcloud-qgis:25.24
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1
RUN pip install --no-warn-script-location --break-system-packages \
      --no-cache-dir \
      git+https://github.com/opengisch/xlsform2qgis.git
COPY project_gen_svc.py /usr/src/app/
CMD ["python3", "/usr/src/app/project_gen_svc.py"]
