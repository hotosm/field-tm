# End-to-end tests

These tests drive whole mapping workflows against the real services in
`compose.test.yaml`, so breakage shows up before manual testing on devices.

```bash
just test e2e        # only these tests
just test backend    # these run as part of the full suite too
```

## What runs today

`test_odk_workflow.py` creates a buildings project through the service layer,
splits it into two tasks and publishes it to ODK Central. `HeadlessCollect`
(`odk_collect.py`) then plays the role of ODK Collect:

1. Decode the project QR code to get the app user's server URL.
2. List the form and download it, its manifest and its entity lists
   (`features.csv`, `tasks.csv`) over OpenRosa.
3. Fill in an instance built from the published form's primary instance, and
   POST it as Collect does.

The test then checks that Central applied the entity update and that the
Field-TM GeoJSON export contains the surveyed building.

A second test validates the QR code settings against Collect's schema
(`collect_settings.schema.json`), also rejecting unknown keys.

`tests/test_xlsforms.py` checks every bundled XLSForm with ODK Validate and
Central.

Limits: `HeadlessCollect` does not evaluate XPath, so the test sets the
calculated fields (`xid`, `xlocation`, entity attributes) by hand. If the form's
calculations change, update the test to match. It reaches Central through
`ODK_CENTRAL_URL` because the public hostname does not resolve in the test stack.

## TODO: future work

Roughly in order of value for effort.

- [ ] **QField headless mapper.** Add the `qfield` profile services to a test
      compose file, then use `qfieldcloud-sdk` as the device: wait for the
      packaging job, download the package, edit a feature in the GeoPackage,
      push a delta, wait for it to apply, and assert the Field-TM export.
- [ ] **PyQGIS checks on the QField package.** In the `qfield-qgis` image,
      open the packaged `.qgs` and assert every layer is valid, form config and
      default/constraint expressions evaluate, and the Field-TM plugin is in
      place. QField runs on QGIS core, so this catches most project breakage.
- [ ] **Re-sync after publish.** Edit the task plan of a published project,
      call `resync_tasks`, and check that a fresh device download sees the new
      tasks while mapped feature statuses survive.
- [ ] **ODK Web Forms form matrix.** Load every form in `xlsforms/` (and the
      Field-TM processed version) in `@getodk/web-forms` via Playwright. Check
      it renders, entity choices load and the produced submission is accepted
      by Central. This tests real XPath evaluation, which `HeadlessCollect`
      skips. Web Forms lacks some Collect features (map widgets), so it does
      not replace Collect testing.
- [ ] **Playwright on the manager UI and planner.** Run project creation
      through the HTMX setup steps and planner task splitting, then reuse the
      resulting project for the device tests above.
- [ ] **QField Linux build smoke test.** Run QField under Xvfb, open a
      downloaded cloud project, and assert from logs (or a marker logged by the
      plugin) that the project and plugin load. Avoid scripting the QML UI,
      it would break often. Check first whether QField desktop can open a
      project from the command line.
- [ ] **Android emulator + ODK Collect, nightly only.** Use
      `reactivecircus/android-emulator-runner` with a Maestro flow: import the
      QR settings, download the form, select a feature on the map, submit.
      Too slow and flaky to block PRs, but it is the only layer that covers
      Collect itself (map selection, settings import).

CI changes for any of these (new workflows, nightly schedules) need
maintainer approval per `AGENTS.md`.
