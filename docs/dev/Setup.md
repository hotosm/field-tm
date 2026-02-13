# Developer Setup Guide

## Overview

The Field-TM stack is now primarily:

1. A LiteStar backend with HTMX + server-rendered templates (code in: `src/backend`)
2. Supporting services:
   - [ODK Central][1] to collect survey submissions.
   - [Minio][13] to serve static content via S3.
   - [Bunkerweb][15] to provide reverse proxying and extra security controls.

### Field-TM Backend

To view more details about the backend click [here][2].

### Field-TM Web UI

The management UI is served directly by the backend templates.

## Prerequisites

- Stable internet connection.
- Git installed on your system.
- Docker and Docker Compose installed on your system.

See further details [here][4]

## Setup: Repository Fork

### 1. Review documentation

Don't forget to review the [Contribution][5]
guidelines and our [Code of Conduct][6]
before contributing!

### 2. Fork the repository

Forking creates a copy of the repository in your own GitHub account.
Go to the
[Field Tasking Manager repository][7]
and click the "Fork" button in the top right corner of the page.

### 3. Navigate to your working directory

Open a terminal and navigate to the directory you want to work in using the
following command:

`cd <work-dir>`

Make sure to replace `<work-dir>` with the name of your directory.

### 4. Clone the forked repository

Clone the forked repository to your local machine using the following command:

`git clone https://github.com/<your-username>/fmtm.git`

Make sure to replace `<your-username>` with your GitHub username.

## Setup: Running Field-TM

See detailed instructions for this step [here][8].

## Setup: Contributing Code

### 1. Create a new branch

Create a new branch for your changes using the following command:

`git checkout -b branch-name`

Make sure to give your branch a descriptive name that reflects the changes
you'll be making.

### 2. Make changes

Make your contribution, run tests where needed and save.

### 3. Add changes

Add the changes you've made using the following command:

`git add <file-name>`

Make sure you replace `<file-name>` with the name of the file you made changes
to.

### 4. Commit and push

Once you've added changes, commit them to your local branch using the following
command:

`git commit -m "Add feature"`

Make sure to write a descriptive commit message that explains the changes you've
made. Then, push your changes to your forked repository using the following
command:

`git push origin branch-name`

### 5. Submit a pull request

Go to your forked repository on GitHub and click the "Pull requests" tab,
then click "Create pull request".

This will open a new pull request in the Field-TM repository, where you can:

- Select the branch you wish to merge into `dev`.
- Describe your changes and request that they be merged into the main codebase.

That's it! You've now contributed to the Field Tasking Manager.

## Alternative Operating Systems

### Windows

Windows Subsystem for Linux (WSL) can be used to run Docker.

This will run a Linux machine inside Windows very efficiently.

To install follow the
[official instructions][11].

Then continue with the Field-TM installation.

### MacOS

[Colima][12] is recommended
to run `docker` and `docker compose` commands.

Install colima, docker, docker compose using brew:

```sh
brew install colima
brew install docker docker-compose
```

Then configure the docker compose plugin to work on MacOS:

```sh
mkdir -p ~/.docker/cli-plugins

ln -sfn $(brew --prefix)/opt/docker-compose/bin/docker-compose ~/.docker/cli-plugins/docker-compose
```

Run Colima:

```sh
colima start
```

Then continue with the Field-TM installation.

> Note: only tagged backend images are multi-architecture, supporting
> MacOS. The regular images for fast continuous deployment are not:
> `backend:dev`, `backend:staging`, `backend:main`.

### A Note on Docker Desktop

While in theory Field-TM should run using Docker-Desktop, it has not
been tested.

The authors opinion is that the official Linux Docker Daemon
should be installed in WSL or MacOS, instead of using Docker Desktop.

> Colima is a wrapper to run the Docker Daemon.

Although Docker Desktop may have a user friendly GUI, it simply
runs docker commands inside a Linux virtual machine underneath.

It is often easier and more flexible to do this yourself.
Plus it gives you access to all other other tools available
in a Linux operating system!

## Help and Support

If you encounter any issues or need assistance while using Field-TM, you can access
the following resources:

- Check the [FAQs][9].
- Message the team in the available
  [slack channel: #field-mapping-tasking-manager][10]

Happy coding!

The Field-TM Developer Team

[1]: https://docs.getodk.org/central-intro
[2]: https://docs.field.hotosm.org/dev/Backend
[3]: https://docs.field.hotosm.org/dev/Frontend
[4]: https://docs.field.hotosm.org/INSTALL/#software-requirements
[5]: https://docs.field.hotosm.org/CONTRIBUTING
[6]: https://docs.hotosm.org/code-of-conduct
[7]: https://github.com/hotosm/field-tm
[8]: https://docs.field.hotosm.org/INSTALL/#setup-your-local-environment
[9]: https://docs.field.hotosm.org/faq
[10]: https://hotosm.slack.com/archives/C04PCBFDEGN
[11]: https://learn.microsoft.com/en-us/windows/wsl/install "official instructions"
[12]: https://github.com/abiosoft/colima "Colima"
[13]: https://min.io
[14]: https://electric-sql.com
[15]: https://www.bunkerweb.io
