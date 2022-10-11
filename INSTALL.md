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

    docker attach field-map-odk-web-1

Add debug line in code

    import ipdb;ipdb.set_trace()

When this line is reached in the code then the attached tty window will 
become interactive with ipdb.



Debugging commands

    help

To get out of debugging

    CTRL + D

## Database

### Database migrations

To migrate, make the changes in models.py
Start docker services `docker compose up`
Attach to web app container `docker compose exec web /bin/bash`
Run migration `FLASK_APP=odk_fieldmap/__init__.py flask db migrate -m "[MIGRATION COMMENT]"`
Upgrade db `FLASK_APP=odk_fieldmap/__init__.py flask db upgrade`

### Access database (psql):

Option #1:

    `docker exec -it field-map-odk-db-1 psql -U fmtm fmtm`

Option #2:

    `docker compose exec db psql --username=fmtm --dbname=fmtm`

And then connect to the database

    `\c fmtm`

A few commands

    List tables: `/d`

If you make a change, don't forget to commit the change!

## Production

### Config:

    cp .env.example .env

Update the .env file with the desired settings.

### Start services:

    docker compose -f docker-compose.prod.yml up -d --build

## Testing

    pip install -r odk_fieldmap/requirements.txt
    python -m pytest

## Troubleshooting

    # list all containers
    docker ps -a

    # turns everything off
    docker compose down
