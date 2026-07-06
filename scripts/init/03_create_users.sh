#!/usr/bin/env bash
set -euo pipefail

psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v dml_user="$POSTGRES_DML_USER" \
  -v dml_pass="$POSTGRES_DML_PASSWORD" <<END

CREATE ROLE :"dml_user" LOGIN PASSWORD :'dml_pass';
GRANT dml_role TO :"dml_user";

END