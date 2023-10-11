# Deployment Flow

These stages go in order, from local development, through to production deployment.

## Local Development

- Devs develop features on their local instance.
- Use `docker-compose.yml` setup for testing.
- Once feature and testing complete, make a PR to the `development` branch.

## Development Deployment

- Once a PR is approved, it is merged to `development`.
- This triggers a workflow to automatically deploy the code changes on the dev server.
- The purpose of this stage is for fast CI,
  i.e. the developer sees their code in action quickly.

## Staging Deployment

- At a set interval (approx bi-weekly),
  the updates made on `development` and frozen, tested,
  patched (if required), and merged into the `staging` branch via PR.
- Once approved, the `staging` branch auto-deploys to the staging server.
- The purpose of this stage is to reguarly release versions of FMTM that
  power users (and the project owner) can test.
- Anyone who doesn't mind occasional breakage is welcome to use this server publically.
- Hot fixes are also possible, if fixing some
  functionality is critical for FMTM to function.

## Production Deployment

- The staging server instance is thoroughly tested
  by the product owner, and bug reports filed.
- The release is hardened into longer interval (approx bi-monthly) production releases.
- A PR is made from `staging` to `main` branch.
- Once approved and the code merged, a Github **release** is made.
- A release is available on Github,
  including all relevant release notes for what has been updated.
- The **release** will trigger the workflow to deploy to the production server.

## Other: Feature Demo Releases

- A feature demo release is a throwaway instance of FMTM with a particular purpose.
- Functionality is developed here for various reasons:
  - Specific updates for a single project that won't be used elsewhere.
  - Very fast updating of the server,
    without interfering with the typical release flow.
- The key point is that these branch instances are **single use**
  and will be **shut down** once the project has ended.
- The easiest approach is probably to:
  - Create and login to a server.
  - Run the bundled `feature-demo.sh` install script.
- Alternatively, a workflow can be made to auto-deploy:
  - Triggering on a branch naming convention: `feature-demo/some-feature`.
  - The user will have to enter an SSH key into the Gitlab secrets.
  - The workflow will deploy to the server remotely
    when the branch is pushed to.
  - This approach is less preferred, as the user
    requires write access to the Github repo,
    but is under consideration.
