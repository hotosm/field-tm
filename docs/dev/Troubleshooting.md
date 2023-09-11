# Troubleshooting 🆘

## Running FMTM standalone

- Although it's easiest to use Docker, sometimes it may no be feasible, or not preferred.
- We use a tool called PDM to manage dependencies.
- PDM can run in two modes: venv and PEP582 (`__pypackages__`).
- Be careful when running FMTM you are not accidentally pulling in your system packages.

### Tips

- If a directory `__pypackages__` exists, delete it and attempt to
  `pdm install`
  again.
- If the `__pypackages__` directory returns, then force using venv instead
  `pdm config python.use_venv true`
  and remove the directory again.
- Troubleshoot the packages PDM sees with:
  `pdm run pip list`
- Check a package can be imported in the PDM-based Python environment:

```bash
pdm run python
import fastapi
```

If you receive errors such as:

```bash
pydantic.error_wrappers.ValidationError: 3 validation errors for Settings
OSM_URL
  field required (type=value_error.missing)
OSM_SCOPE
  field required (type=value_error.missing)
OSM_LOGIN_REDIRECT_URI
  field required (type=value_error.missing)
```

Then you need to set the env variables on your system.

If you would rather not do this,
an alternative can be to feed them into the pdm command:

```bash
FRONTEND_MAIN_URL="" FRONTEND_MAP_URL="" \
OSM_CLIENT_ID="" OSM_CLIENT_SECRET="" OSM_SECRET_KEY="" \
pdm run uvicorn app.main:api --host 0.0.0.0 --port 8000
```
