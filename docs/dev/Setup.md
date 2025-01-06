# Developer Setup Guide

## Overview

The FMTM can be divided into four parts:

1. An API backend in FastAPI (code in: `src/backend`)
2. A desktop-based management frontend website in React (code in: `src/frontend`)
3. A mobile-based mapper frontend website in Svelte (code in: `src/mapper`)
4. Supporting services that tie everything together, such as [ODK Central][1]
   for collecting submission data, and an S3 service for storing files.

### FMTM Backend

To view more details about the backend click [here][2].

### FMTM Frontend

To view more details about the frontend click [here][3].

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
[Field Mapping Tasking Manager repository][7]
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

## Setup: Running FMTM

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

This will open a new pull request in the FMTM repository, where you can:

- Select the branch you wish to merge into `development`.
- Describe your changes and request that they be merged into the main codebase.

That's it! You've now contributed to the Field Mapping Tasking Manager.

## Help and Support

If you encounter any issues or need assistance while using FMTM, you can access
the following resources:

- Check the [FAQs][9].
- Message the team in the available
  [slack channel: #field-mapping-tasking-manager][10]

Happy coding!

The FMTM Developer Team

[1]: https://docs.getodk.org/central-intro
[2]: https://docs.fmtm.dev/dev/Backend
[3]: https://docs.fmtm.dev/dev/Frontend
[4]: https://docs.fmtm.dev/INSTALL/#software-requirements
[5]: https://docs.fmtm.dev/CONTRIBUTING
[6]: https://docs.hotosm.org/code-of-conduct
[7]: https://github.com/hotosm/fmtm
[8]: https://docs.fmtm.dev/INSTALL/#setup-your-local-environment
[9]: https://docs.fmtm.dev/faq
[10]: https://hotosm.slack.com/archives/C04PCBFDEGN
