# Access the database (psql)

**Option 1** (when the docker container is running) use this command to access it through the local psql using the below command:

    `psql -d fmtm -U fmtm -h localhost`

**Option 2** (when running the database in Docker) use this command to access the
PostgreSQL shell inside the fmtm-db-1 container and interact with the fmtm database 
using the psql command-line interface:

    `docker exec -it fmtm-db-1 psql -U fmtm fmtm`

And then connect to the database using this command : 

    `\c fmtm`

## To access the fmtm database using psql, follow the instructions below

### A few helpful psql commands

- Open a terminal window and run the following command:

        docker exec -it fmtm-db-1 psql -U fmtm fmtm

  This will open the psql command-line interface and connect you to the fmtm database.

- Once connected to the fmtm database, you can switch to a different database using the command:

        \c dbname

  Replace "dbname" with the name of the database you want to switch to. forexample `\c fmtm`

- You can list all the databases using the command:

        \l

- To list all the schemas of the currently connected database, use the command:

        \dn

- To list all the functions in the current database, use the command:

        \df

- To list all the views in the current database, use the command:

        \dv

- To list all the users and roles, use the command:

        \du

- To list all the tables in the current database, use the command:

        \dt

- To describe a table, use the command:

        \d table_name

  Replace "table_name" with the name of the table you want to describe.

- To execute the last command again, use the command:

        \g

- To view your command history, use the command:

        \s

- To save your command history to a file, use the command:

        \s filename

  Replace "filename" with the name of the file you want to save the command history to.

- To execute commands from a file, use the command:

        \i filename

  Replace "filename" with the name of the file containing the commands you want to execute.

- To view a list of all psql commands, use the command:

        \?

- To view help for a specific command, use the command:

        \h command_name

  Replace "command_name" with the name of the command you want help with.

- To exit psql, use the command:

        \q

**Note:** If you make a change, don't forget to commit the change!

# Migrations

Migrations are a way to manage changes to the database schema over time. We haven't yet implemented migrations in fmtm, but if you need to drop all tables, you can use the following commands while connected to the fmtm database:

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

**Note:** Remember to use caution when dropping tables, as this will permanently delete all data in those tables. If you make any changes to the database, be sure to commit them to ensure that they are saved.
