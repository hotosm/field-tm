# Troubleshooting 🆘

## Running Field-TM standalone

- Although it's easiest to use Docker, sometimes it may no be feasible, or
  not preferred.
- We use a tool called `uv` to manage dependencies.
- Be careful when running Field-TM you are not accidentally pulling in your
  system packages.

### Tips

- Troubleshoot the packages `uv` sees with:
  `uv pip list`
- Check a package can be imported in the uv-based Python environment:

  ```bash
  uv run python
  import fastapi
  ```

If you receive errors such as:

```bash
pydantic.error_wrappers.ValidationError: 3 validation errors for Settings
OSM_URL
  field required (type=value_error.missing)
OSM_SCOPE
  field required (type=value_error.missing)
```

Then you need to set the env variables on your system.

Alternatively, run via `just`:

```bash
just start backend-no-docker
```
