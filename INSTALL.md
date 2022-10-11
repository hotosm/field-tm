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

Access database (psql):

    docker exec -it field-map-odk-db-1 psql -U fmtm fmtm

Debugging commands

    help

To get out of debugging

    CTRL + D

## Production

### Config:

    cp .env.example .env

Update the .env file with the desired settings.

### Start services:

    docker compose -f docker-compose.prod.yml up -d --build

### Access database:

    docker compose exec db psql --username=fmtm --dbname=fmtm

## Testing

    pip install -r odk_fieldmap/requirements.txt
    python -m pytest

## Troubleshooting

    # list all containers
    docker ps -a

    # turns everything off
    docker compose down
