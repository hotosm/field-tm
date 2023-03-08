# Frontend Deployment for Development


## The Microfrontend configuration
The Field Mapping Tasking Manager is a web application that helps users coordinate mapping efforts in OpenStreetMap. It is built using a microfrontend architecture, which means that the application is composed of multiple small frontend modules that can be developed, tested, and deployed independently.

FMTM uses Webpack remote modules to dynamically load code from other microfrontend applications, which allows developers to develop, test, and deploy smaller and more manageable parts of code independently. This improves the performance and scalability of the application.

List of current microfrontend modules:
- **main**:
  - Description: The main frontend, displays projects and tasks.
  - Port: 8080.
- **fmtm_openlayers_map**:
  - Description: The map component, displays tasks on a map.
  - Port: 8081.

## Setting up the development environment
### 1. Get the project code
  Clone the Field Mapping Tasking Manager repository from GitHub using the following command:

`git clone https://github.com/hotosm/tasking-manager.git`

### 2. Install dependencies
  Navigate to the react frontend directory: `cd src/frontend/main` 
  
  Install the dependencies by running the following command: `npm install`

### 3. Run the project
You can run each microfrontend independently in a separate terminal (with a `npm install` & `npm run start:live`).

Each microfrontend should now be accessible at: <http://127.0.0.1:8080>.

However, the easiest option would be to use docker.

### 4. Make changes
You can now make changes to the codebase and see the changes reflected in your browser. The development server automatically refreshes the page when changes are saved.

## Contribute to the frontend 
 Don't forget to review the [Contribution](https://github.com/hotosm/fmtm/wiki/Contribution) guidelines and our [Code of Conduct](https://github.com/hotosm/fmtm/wiki/Code-of-Conduct) before contributing!
Here are the steps to contribute to the frontend of Field Mapping Tasking Manager:

### 1. Fork the repository
Fork creates a copy of the repository in your own GitHub account. 
Go to the [Field Mapping Tasking Manager repository](https://github.com/hotosm/fmtm) and click the "Fork" button in the top right corner of the page.

### 2. Clone the forked repository
Clone the forked repository to your local machine using the following command:

`git clone https://github.com/<your-username>/tasking-manager.git`

Make sure to replace <your-username> with your GitHub username.

### 3. Create a new branch
Create a new branch for your changes using the following command:

`git checkout -b branch-name`
  
Make sure to give your branch a descriptive name that reflects the changes you'll be making.

### 4. Make changes
Make your changes to the codebase.
  
### 5. Commit and push
Once you've made and tested your changes, commit them to your local branch using the following command:

`git commit -m "Add feature"`
  
Make sure to write a descriptive commit message that explains the changes you've made. Then, push your changes to your forked repository using the following command:

`git push origin branch-name`
  
### 6. Submit a pull request
Go to your forked repository on GitHub and click the "New pull request" button. Select the branch that contains your changes, then click "Create pull request". This will open a new pull request in the Field Mapping Tasking Manager repository, where you can describe your changes and request that they be merged into the main codebase.
  
  
That's it! You've now contributed to the frontend of the Field Mapping Tasking Manager.

## Deployment
  The recommended way to run FMTM is with Docker. You can also develop on your local machine outside of Docker, see below.

> NOTE: If you haven't yet downloaded the Repository and setup your environment variables, please check the [Development]() wiki page.

Now let's get started!

## 1. Start FMTM with Docker

The easiest way to get up and running is by using the FMTM Docker deployment. Docker creates a virtual environment, isolated from your computer's environment, installs all necessary dependencies, and creates a container for each the database, the api, and the frontend. These containers talk to each other via the URLs defined in the docker-compose file and your env file.

### 1A: Starting the Containers

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory of the FMTM project.
3. From the command line run: `docker compose build`
4. Once everything is built, from the command line run: `docker compose up -d ui-main ui-map`

5. If everything goes well you should now be able to **navigate to the project in your browser:**
   - **Frontend:** <http://127.0.0.1:8080>
