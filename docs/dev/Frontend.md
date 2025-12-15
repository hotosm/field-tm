# Frontend Deployment for Development

## 1. Start the Frontend with Docker

This is the easiest way to manage all of the services together.

### 1A: Starting the API Containers

For details on how to run the API first, please see:
[Backend Docs](https://docs.field.hotosm.org/dev/Backend)

### 1B: Starting the Frontend Containers

1. You will need to [Install Docker](https://docs.docker.com/engine/install/)
   and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory of the Field-TM project.
3. From the command line run: `docker compose build ui`
   This is essential, as the development container for the frontend is
   different to production.
4. Once everything is built, from the command line run: `docker compose up -d ui`

5. If everything goes well you should now be able to
   **navigate to the project in your browser:**
   [http://fmtm.localhost:7050](http://fmtm.localhost:7050)

> Note: during development, if you rebuild the frontend, then
> run 'docker compose up -d', the node_modules directory may
> not be updated. To solve this, use the flag:
> --renew-anon-volumes on docker compose up.

## 2. Start the Frontend locally

To run the frontend locally, connected to the staging server as a backend:

```bash
just start frontend-dev
```

The mapper frontend can be started with a similar command:

```bash
just start mapper-frontend-dev
```

## Frontend Tips

The frontend is built with React and Typescript. Here are some tips on how to
work with the frontend:

### Adding Environment Variables

To add environment variables, create a .env.local file in the `src/frontend`
directory. Any variables defined here will override those in `.env`.

### Adding New Routes

To add a new route, create a new page in the src/frontend/pages
directory. Then add a new entry to the `src/frontend/router.tsx` file.

### Adding New Components

To add a new component, create a new .tsx file in the src/frontend/
components directory.

## Frontend Testing

To run the frontend tests locally, run:

```bash
just test frontend
```

> View the HTML report at: `http://localhost:9323`.

To run the Field-TM UI for interactive testing, run:

```bash
just test frontend-e2e-interactive
```
