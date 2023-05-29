# Frontend Deployment for Development

## The Microfrontend configuration

The FMTM frontend is built using a microfrontend architecture, divided into modules that can be developed, tested, and deployed independently.

Webpack remote modules are used to achieve this, dynamically loading code from other microfrontend applications.

In theory, this should improve the performance and scalability of the application.
However, great care should be taken with watching dependency versions across modules, to prevent loading more js content than is required.

List of current microfrontend modules:

- **main**:
  - Description: The main frontend, displays projects and tasks.
  - Location: src/frontend/main
  - Port: 8080.
- **fmtm_openlayers_map**:
  - Description: The map component, displays tasks on a map.
  - Location: src/frontend/fmtm_openlayers_map
  - Port: 8081.

## 1. Start the Frontends with Docker

This is the easiest way to manage multiple frontends at once.

### 1A: Starting the API Containers

For details on how to run the API first, please see: [DEV 2. Backend](https://github.com/hotosm/fmtm/wiki/DEV-2.-Backend)

### 1B: Starting the Frontend Containers

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory of the FMTM project.
3. From the command line run: `docker compose build ui-main ui-map`
   This is essential, as the development containers for the frontend are different to production.
4. Once everything is built, from the command line run: `docker compose up -d ui-main ui-map`

5. If everything goes well you should now be able to **navigate to the project in your browser:**
   - **Main:** <http://127.0.0.1:8080>
   - **Map:** <http://127.0.0.1:8081>

## 2. Start the Frontends locally

### 2A: Navigate to the module subdirectory

See [here](#the-microfrontend-configuration) for the module location.

### 2B: Install dependencies

Install the dependencies by running the following command: `npm install`

### 2C. Run the project

Run the microfrontend with hot-reloading: `npm run start:live`

The frontend should now be accessible at: <<<<<<http://127.0.0.1:<PORT_NUMBER>>>>>>>.

### 2D. Repeat for each module

Each module in the microfrontend must be running for it to operate as a whole.

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

### Conclusion

Running the FMTM project is easy with Docker. You can also run the
project locally outside of Docker, but it requires more setup. The
frontend is built with React and Typescript, and the backend is built
with FastAPI. Use the tips provided to customize and extend the
functionality of the project.
