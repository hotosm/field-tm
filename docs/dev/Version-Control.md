# Version Control

- FMTM uses semantic versioning: MAJOR.MINOR.PATCH.

- The versioning is the same for both the backend and frontend.

- Versions are managed by Commitizen from the `src/backend/pyproject.toml` file.

- Versions are determined by conventional commit messages:
  - `fix: xxx` denotes a patch, `feat: xxx` denotes a minor increment.
  - Breaking changes would typically denote a major increment.
  - This does not necessarily apply to web apps, so major versioning is subjective.

## Bumping Versions

Install commitizen:

```bash
pip install commitizen
```

Bump the version:

```bash
cd src/backend
cz bump --check-consistency --changelog
git push
git push --tag
```
