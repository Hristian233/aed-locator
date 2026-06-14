-- Fix "permission denied for table reports" when the app DB user differs from
-- the migration owner. Run as a PostgreSQL superuser (e.g. postgres):
--
--   psql -U postgres -d aed_locator -f scripts/grant_reports_privileges.sql
--
-- Replace "aed" below if your app user has a different name.

ALTER TABLE reports OWNER TO aed;
ALTER SEQUENCE reports_id_seq OWNER TO aed;
GRANT USAGE ON TYPE reportstatus TO aed;
