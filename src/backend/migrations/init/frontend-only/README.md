# Frontend DB Models

- A few models a neither shared between the backend / frontend, or
  present on the backend database at all.
- We need some 'frontend-only' models for the following purpose:
  - `projects`: a limited subset of synced projects, based on the
    users access level to view the projects (particularly for private
    projects).
  - `api_submissions`: an offline store of POST requests made against
    the backend while offline. These requests are iterated and send
    when the user has connectivity restored.
