FROM redash/redash:26.3.0

COPY --chown=redash:redash dashboard.css /app/client/dist/dashboard.css
COPY --chown=redash:redash customize_frontend.py /app/customize_frontend.py

RUN python /app/customize_frontend.py