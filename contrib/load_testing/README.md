# Load Testing

Utils for load testing the API.

Use `k6s` via the Justfile:

```bash
just test load /project/summaries
```

Or alternatively, install the great [oha](https://github.com/hatoo/oha) CLI,
and simply run a command like:

```bash
oha http://api:8000/projects/199/minimal?project_id=199 -z 60sec
```
