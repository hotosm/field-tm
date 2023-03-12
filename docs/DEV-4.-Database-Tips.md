# Access the database (psql)

Option #1 (when running the database in Docker):

    `docker exec -it fmtm-db-1 psql -U fmtm fmtm`

And then connect to the database

    `\c fmtm`

## A few helpful psql commands

    Switch connection to the new database: `\c dbname`
    List databases: `\l`
    List all schemes of currently connected database: `\dn`
    List functions of current database: `\df`
    List views in current database: `\dv`
    List users and roles: `\du`

    List tables: `\dt`
    Describe a table: `\d table_name`

    Last command again: `\g`
    Command history: `\s`
    Save command history to file: `\s filename`
    Execute commands from file: `\i filename`
    List psql commands: `\?`
    Help: `\h`
    Exit: `\q`

If you make a change, don't forget to commit the change!

# Migrations

We haven't yet implemented migrations.

If you need to drop all tables, connect to fmtm and...

    drop table mapping_issue_categories cascade;
    drop table organisation_managers cascade;
    drop table organisations  cascade;
    drop table project_allowed_users cascade;
    drop table project_chat cascade;
    drop table project_info cascade;
    drop table project_teams cascade;
    drop table projects cascade;
    drop table task_history cascade;
    drop table task_invalidation_history cascade;
    drop table task_mapping_issues cascade;
    drop table tasks cascade;
    drop table teams cascade;
    drop table user_licenses cascade;
    drop table users cascade;
    drop table x_form cascade;
