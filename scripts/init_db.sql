-- Enable Apache AGE in the current database and make Cypher usable in this session.
-- Run against the project database (default: age101).

CREATE EXTENSION IF NOT EXISTS age;

LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Graphs are (re)created idempotently by src/age/load.py (`make load`); this is just
-- a smoke check that create_graph works right after install.
SELECT create_graph('smoke_check');
SELECT drop_graph('smoke_check', true);
