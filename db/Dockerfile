FROM postgres:14-alpine

COPY init.sql /docker-entrypoint-initdb.d/
RUN mkdir -p /oracle/pg_data/archive/ && \
    chown -R postgres:postgres /oracle/pg_data/archive/