# Installation

## Software Requirements

It is recommended to run Field-TM on a Linux-based machine.

> This includes MacOS, but some [tools must be substituted][1].
>
> For Windows users, the easiest option is to use [Windows Subsystem for Linux][2]

Before you can install and use this application, you will need to have
the following software installed and configured on your system:

> If running Debian/Ubuntu, the install script below does this for you.

[Git][3] to clone the Field-TM repository.

[Docker][4]
to run Field-TM inside containers.

[Docker Compose][5]
for easy orchestration of the Field-TM services.

> This is Docker Compose V2, the official Docker CLI plugin.
>
> i.e. `docker compose` commands, not `docker-compose` (the old tool).

## Easy Install

On a Linux-based machine with `bash` installed, run the script:

> Note: it is best to run this script as a user other than root.
>
> However, if you run as root, a user svcfmtm will be created for you.

```bash
curl -L https://get.field.hotosm.org -o install.sh
bash install.sh

# Then follow the prompts
```

## Manual Install

If more details are required, check out the
[dev docs][6]

### Clone the Field-TM repository

Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/hotosm/field-tm.git

# If you wish to deploy for production, change to the main branch
git checkout main
```

### Setup Your Local Environment

These steps are essential to run and test your code!

#### 1. Setup OSM OAuth 2.0

The Field-TM uses OAuth with OSM to authenticate users.

To properly configure your Field-TM project, you will need to create keys for OSM.

1. [Login to OSM][7]
   (_If you do not have an account yet, click the signup
   button at the top navigation bar to create one_).

   Click the drop down arrow on the top right of the navigation bar
   and select My Settings.

2. Register your Field-TM instance to OAuth 2 applications.

   Put your login redirect url as `http://127.0.0.1:7051/osmauth` if running locally,
   or for production replace with https://{YOUR_DOMAIN}/osmauth

   > Note: `127.0.0.1` is required for debugging instead of `localhost`
   > due to OSM restrictions.

   ![image][8]

3. Add required permissions:
   - 'Read user preferences' (`read_prefs`)
   - 'Send private messages to other users' (`send_messages`)

4. Now save your Client ID and Client Secret for the next step.

#### 2. Create a dotenv file

Environmental variables are used throughout this project.
To get started, create `.env` file in the top level dir,
a sample is located at `.env.example`.

This can be created interactively by running:

```bash
just config generate-dotenv
```

> Note: If extra cors origins are required for testing, the variable
> `EXTRA_CORS_ORIGINS` is a set of comma separated strings, e.g.:
> <http://fmtm.localhost:7050,http://some.other.domain>

#### 3. Deploy using Just

```bash
just start prod
```

### Setup ODK Central User (Optional)

The Field-TM uses ODK Central to store ODK data.

- By default, the docker setup includes a Central server.
- The credentials should have been provided in your `.env`
  file to automatically create a user.
- To create a user manually:

```bash
docker compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-create
docker-compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-promote
```

> Note: Alternatively, you may use an external Central server and user.

### Set Up Monitoring (Optional)

- There is an optional configuration for application monitoring via OpenTelemetry.
- To enable this set in your `.env` file:

  ```dotenv
  # For OpenObserve
  MONITORING="openobserve"
  # For Sentry
  MONITORING="sentry"
  ```

- Check the `.env.example` for additional required parameters.
- Everything should be configured for you to see endpoint calls in the
  selected web dashboard, providing full error tracebacks and stats.

### Check Authentication (Optional)

Once you have deployed, you will need to check that you can properly authenticate.

1. Navigate to your frontend (e.g. `http://fmtm.localhost:7050`)

2. Click the 'Sign In' button and follow the popup prompts.

3. If successful, you should see your username in the header.

4. If you see an error instead, double check your credentials and
   redirect URL in the openstreetmap.org settings.

### Configure Custom Favicon

- During deploy, place your `favicon.svg` in the root of the repo.
- Run the deployment script, and the favicon + generated PNG version
  will be used in your frontend deployment automatically.

That's it, you have successfully set up Field-TM!!

[1]: ./dev/Setup.md#alternative-operating-systems "MacOS container tools"
[2]: ./dev/Setup.md#alternative-operating-systems "Windows Subsystem for Linux"
[3]: https://git-scm.com/ "Git"
[4]: https://docs.docker.com/engine/install/ "Docker"
[5]: https://docs.docker.com/compose/install "Docker Compose"
[6]: https://docs.field.hotosm.org/dev/Setup/ "dev docs"
[7]: https://www.openstreetmap.org/login "Login to OSM"
[8]: https://user-images.githubusercontent.com/36752999/216319298-1444a62f-ba6b-4439-bb4f-2075fdf03291.png "image"
