FROM apache/airflow:3.3.0

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

COPY --chown=airflow:root pyproject.toml /opt/airflow/project/
COPY --chown=airflow:root src /opt/airflow/project/src

RUN pip install --no-cache-dir /opt/airflow/project

USER root

RUN /home/airflow/.local/bin/playwright install --with-deps chromium \
    && chmod -R a+rX /opt/playwright

USER airflow