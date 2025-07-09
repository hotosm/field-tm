# Making Releases

- Typically `dev` would have been merged into `staging`, and code
  in `staging` thoroughly tested.
- Once everything is verified to be working, a release can be made.
- Normally I would do a simple hard reset of `main` to the latest
  tested `staging` (ensure all cherry-picked hotfixes are also
  present on staging in this case):

  ```bash
  git checkout main
  git reset --hard origin/staging
  ```

## Checklist

To make a new release of Field-TM, ensure the following is done:

1. Code is pulled through to the `main` branch.
2. Enter the backend directory: `cd src/backend`.
3. Bump the version: `cz bump --check-consistency`
   - To make manual control of which version to bump, the
     `--increment PATCH` or `--increment MINOR` flag can be
     used.
4. If the uv.lock file is relocked and breaks the commit,
   then commit manually by copying the commit message printed
   to the terminal:
   `git commit -m "bump: 2025.1.1 --> 2025.1.2"`
   then ensure the tag is present
   `git tag 2025.1.2`
5. Push the latest commits and tag:
   `git push && git push --tag`
6. Create a new release on Github via the UI, based on the new
   tag.
7. Ensure the
   [Github workflow](https://github.com/hotosm/field-tm/actions/workflows/tag_build.yml)
   succeeds in creating the latest tagged image.
