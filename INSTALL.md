## Development

### Config:

    cp .env.example .env

Update the .env file with the desired settings.

### Start Services:

    docker compose up --build

#### To put it in the background:

    docker compose up --build -d
 

### Debugging

Open tty to container

    docker attach fmtm-web-1

Add debug line in code

    import ipdb;ipdb.set_trace()

When this line is reached in the code then the attached tty window will 
become interactive with ipdb.

A few of those commands:
    [Command CheatSheet](https://wangchuan.github.io/coding/2017/07/12/ipdb-cheat-sheet.html)
    h(elp)
    w(here)
    d(own)
    u(p)
    b(reak): [ ([filename:]lineno | function) [, condition] ]
    tbreak: [ ([filename:]lineno | function) [, condition] ]
    cl(ear): [bpnumber [bpnumber ...] ]
    disable bpnumber: [bpnumber ...]
    enable bpnumber: [bpnumber ...]
    ignore bpnumber count
    condition bpnumber condition
    s(tep)
    n(ext)
    unt(il)
    r(eturn)
    run [args ...]
    c(ont(inue))
    l(ist): [first [,last]]
    a(rgs)
    p expression


Debugging commands

    help

To get out of debugging

    CTRL + D

## Database

### Database migrations

To migrate, make the changes in models.py
Start docker services `docker compose up`
Attach to web app container `docker compose exec web /bin/bash`
Run migration `FLASK_APP=src/web/__init__.py flask db migrate -m "[MIGRATION COMMENT]"`
Upgrade db `FLASK_APP=src/web/__init__.py flask db upgrade`

### Access database (psql):

Option #1:

    `docker exec -it fmtm-db-1 psql -U fmtm fmtm`

Option #2:

    `docker compose exec db psql --username=fmtm --dbname=fmtm`

And then connect to the database

    `\c fmtm`

A few commands

    Switch connection to new database: `\c dbname`
    List databases: `\l`
    List all schemes of currently connected database: `\dn`
    List functions of current database: `\df`
    List views in current datbase: `\dv`
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

If you haven't implemented migrations yet and need to drop all tables, connect to fmtm and...

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

## Production

### Config:

    cp .env.example .env

Update the .env file with the desired settings.

### Start services:

    docker compose -f docker-compose.prod.yml up -d --build

## Testing

    pip install -r src/web/requirements.txt
    python -m pytest

## Troubleshooting

    # list all containers
    docker ps -a

    # turns everything off
    docker compose down
