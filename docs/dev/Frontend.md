# Frontend Deployment for Development

## 1. Start the Frontend with Docker

This is the easiest way to manage all of the services together.

### 1A: Starting the API Containers

For details on how to run the API first, please see:
[Backend Docs](https://hotosm.github.io/fmtm/dev/Backend)

### 1B: Starting the Frontend Containers

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory of the FMTM project.
3. From the command line run: `docker compose build ui`
   This is essential, as the development container for the frontend is different to production.
4. Once everything is built, from the command line run: `docker compose up -d ui`

5. If everything goes well you should now be able to **navigate to the project in your browser:** <http://fmtm.localhost:7050>

> Note: during development, if you rebuild the frontend, then
> run 'docker compose up -d', the node_modules directory may
> not be updated. To solve this, use the flag:
> --renew-anon-volumes on docker compose up.

## 2. Start the Frontend locally

### 2A: Navigate to the frontend subdirectory

`cd src/frontend`

### 2B: Install dependencies

`npm install`

### 2C. Run the project

Run the frontend with hot-reloading: `npm run start:live`

The frontend should now be accessible at: `http://127.0.0.1:<PORT_NUMBER>`

## Frontend Tips

The frontend is built with React and Typescript. Here are some tips on how to work with the frontend:

### Adding Environment Variables

To add environment variables, create a .env.local file in the `src/frontend`
directory. Any variables defined here will override those in `.env`.

### Adding New Routes

To add a new route, create a new page in the src/frontend/pages
directory. Then add a new entry to the `src/frontend/router.tsx` file.

### Adding New Components

To add a new component, create a new .tsx file in the src/frontend/
components directory.

## Conclusion

Running the FMTM project is easy with Docker. You can also run the
project locally outside of Docker, but it requires more setup. The
frontend is built with React and Typescript, and the backend is built
with FastAPI. Use the tips provided to customize and extend the
functionality of the project.
