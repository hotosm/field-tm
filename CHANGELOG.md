# Changelog

## 2025.6.1 (2025-10-23)

### Feat

- **mapper**: add basemap loader to 'more' section for custom imagery
- init qfield org and user at startup
- **mapper**: allow mapper to view existing collected data from last submission (#2860)
- **backend**: add option to include media in submission JSON download (#2823)
- **backend**: save QField server creds (#2849)
- **osm-fieldwork**: make the photo upload required=True or False (configurable)
- **backend**: add endpoint to check if qfield cloud credentials are valid

### Fix

- **area-splitter**: remove accidentally added loguru dep to area-splitter db
- **osm-fieldwork**: ensure start-geopoint question is removed from qfield xlsform
- **qfield**: fix qfield worker wrapper (for processing qfield project file)
- **package**: expose python package scripts to uv command runner
- **backend**: QField Project creation fixes (#2864)
- **qfield**: correct QFieldCloud credentials test endpoint to use QField instead of ODK
- **qfield**: fix the redirect QFieldCloud URL.
- **mapper**: allow setting primaryLocale on mapper frontend config
- **createProject**: on qfield select and generate-project-data success, redirect user to qfield cloud dashboard (#2861)
- **mapper**: ordering of dialogs to confirm mapping complete
- **mapper**: make translations clearer for total features mapped checj
- **mapper**: remove broken stamen black&white basemap
- **mapper**: add translations for all map controls
- **mapper**: add translations for all maplibre control tooltips
- **mapper**: alignment of 'got it' button text in geolocation dialog
- **mapper**: replace icons for new point and delete point
- **mapper**: brazillian portuguese proceed translation all caps
- **mapper**: add translation for project home page
- **mapper**: add configurable tabTitle for mapper frontend (page title)
- **mapper**: login dialog for private projects, if not logged in (#2852)
- **mapper**: add clearer text highlighting for initial instructions
- **backend**: do not error if featcol has no properties key multi --> single geom
- **createProjectService**: throw error and stop project creation if any of the project creation apis fail (#2846)
- **backend**: qfield geometry validation in project creation service
- **backend**: comment out psycopg otel instrumentor for now
- **backend**: remove psycopg opentelemetry instrumentation until fixed
- **backend**: init of db on server startup
- update init order for db pool initialisation
- **backend**: init of loguru in the database init file

### Refactor

- **osm-fieldwork**: converted xlsforms to .yaml for better version control (#2865)
- remove QFIELDCLOUD_ORG_NAME var
- **qfield**: hide QFieldCloud password using secrets instead of plain text

## 2025.6.0 (2025-09-28)

### Feat

- **backend**: add endpoint to retry qfield project generation
- **osm-fieldwork**: add function to append task_id choices to form after created
- **backend**: QField Cloud integration (#2828)
- **frontend**: Refactor landing page according to feedback (#2831)
- **submission**: Add endpoint to edit existing submissions. (#2820)
- **backend**: allow setting cookie domains not using subdomains (#2822)
- **project**: add 'use_st_within' option for data extraction and update form handling (#2807)

### Fix

- **backend**: create qfield project with no spaces in the name
- **backend**: correctly set qfieldcloud project owner to HOTOSM org
- **backend**: set qfieldcloud client with token explicitly
- **createProject**: update use_odk_collect state during stub project creation (#2839)
- **backend**: improving logs for qfield project creation, login on demand only
- **osm-fieldwork**: hook urllib logger when LOG_LEVEL=DEBUG
- **qfield**: handle spaces in project name for final qgis project file
- **backend**: log the final qfield project file location
- **mapper**: do not enable webforms when mapping app selection = ODK or QField
- **backend**: usage of aiohttp for qfield project creation
- **backend**: add task_filter question to ODK Collect workflow offline
- **backend**: handling of multipolygons with z dimension (e.g. from qgis)
- **backend**: fail gracefully if project location_str extraction fails
- **frontend**: missed isProjectDeletePending app selector
- **backend**: do not fails to start api if QField creds are incorrect
- **backend**: use aiohttp vs httpx for qfield cloud calls
- **backend**: using FMTM_DEV_PORT locally
- fixes #2825 modularlise area-splitter package algorithm
- **backend**: set correct domain for expiring cookies
- **backend**: also correctly set cookie domain for osm cookie
- **backend**: reference to FMTM_MAPPER_DOMAIN in config.py
- **mapper**: add matomo tracking via config.json param

### Refactor

- **backend**: swap redirectresponse --> jsonresponse qfield project dash url
- **mapper**: minor typing issue
- remove details about custom odk application
- remove old scripts from repo, reorganise
- fix area-splitter current version
- fixes #2796 full migration of fmtm-splitter as workspace
- replace all reference fmtm.dev --> fieldtm.hotosm.org

## 2025.5.0 (2025-08-28)

### Feat

- **mapper**: hot matomo tracking component add (#2788)
- **frontend**: merge AOI by default on upload during proj create (#2782)
- **frontend**: Update task list after task event action (#2783)
- **backend**: add merge choice during project creation and default visibility (#2779)
- **frontend**: Task User Assignment (#2775)
- **mapper**: remove 'Offline' & Add 'My Tasks' section (#2773)
- **organisation**: Add project status in organisation stats. (#2771)
- **backend**: org based submission download and infographics (#2689)
- **mapper**: clustering if primary geoms are point & update point icon (#2555)

### Fix

- **tasks**: correct assignee_sub variable in add_new_task_event function (#2802)
- **backend**: fix mapper access to assigned task in private project. (#2795)
- **mapper**: skipping of feature_exists questions for new geoms
- **backend**: add more information to logs on /stub creation failure
- **frontend**: Restrict mappers to update task  (#2780)
- **migration**: Fix broken migration of project visibility. (#2774)
- **backend**: search functionality when query includes space. (#2767)
- **mapper**: web-forms fixed option image display (#2765)

### Refactor

- **mapper**: upgrade hotosm/ui package on mapper frontend (#2797)
- **backend**: project visibility removing SENSITIVE and INVITE_ONLY (#2772)
- **frontend**: replace API usage and types with Tanstack Query (#2768)
- **mapper**: add status filter add to project summary and other minor refactors (#2763)

## 2025.4.3 (2025-08-01)

### Feat

- **OdkCentral**: add async method to retrieve submission XML content (#2759)

### Fix

- **backend**: backend part to allow listing of required media from uploaded XLSForm (#2738)
- **mapper**: bad geometry layer & layer unselectable on manual sync issue (#2757)
- **mapper**: avoid parse of submission XML to string in memory, towards #2740
- **styles**: make task & entity entity dialog title bold and primary color (#2748)
- **main**: wrap geolocation inside toggleLayer condition to retain location layer after baselayer switch (#2747)

## 2025.4.2 (2025-07-30)

### Feat

- **mapper**: remove pglite, rely on svelte store + electric sync (#2732)

### Fix

- **frontend**: include credentials when getting form media
- **validation**: UI crash on AOI reset & continue next (#2734)

## 2025.4.1 (2025-07-26)

### Feat

- Role unassign from project and odk cred check endpoint (#2708)
- **json-models**: Added json model of each yaml data models
- progressive project creation workflow draft / published (#2680)
- update project creation to use PATCH method and add stub project fixture for testing
- add duplicate project name check during patch project creation
- update project creation to use PATCH method and add stub project fixture for testing
- add duplicate project name check during patch project creation
- add highways.xlsx in osm-fieldwork and osm_category in frontend
- **backend**: Replace osm_rawdata with raw_data_api_py adding highway category

### Fix

- **models**: fix project visibility to exclude draft projects for cross organisation manager (#2731)
- **mapper**: fix features not updating acc to extent click after baselayer change by remounting layer (#2728)
- use st intersects for linear geoms during project file generation (#2715)
- **frontend**: use global extent for Line geometry & other fixes (#2711)
- update project API endpoint to use project ID in URL (#2710)
- **backend**: avoid slash in data extract file name
- **backend**: pass access token to generate osm extracts
- questions wont be skipped for new entity worflow (#2707)
- **frontend**: project creation bugs & refactor (#2692)
- **pytest**: remove print statement
- **pytest**: fix the fixture name and user in submission
- **projects**: fix total contributions mismatch in infographics (#2691)
- **backend**: add mapping mode options and fix standard odk collect workflow (#2690)
- **mapper**: correctly set extent for fgb polyline to undefined
- **mapper**: towards #2663, fix linestring display for mapper frontend
- **mapper**: load initial entity db records prior to sync
- **pytest**: update pytest function test_get_contributors with proper assert and fixture
- **projects**: fix total contributions mismatch in infographics (#2691)
- **backend**: add mapping mode options and fix standard odk collect workflow (#2690)
- **mapper**: correctly set extent for fgb polyline to undefined
- **mapper**: towards #2663, fix linestring display for mapper frontend
- **mapper**: load initial entity db records prior to sync
- **xlsform**: update conflict changes with dev branch
- **xlsform**: update conflict changes with dev branch
- **data-models**: fixed the syntax error in models.yaml file
- **backend**: create valid geojson from javarosa, update osm conflation with raw-data-api-py
- **main**: dont select existing entity if new entity draw mode is enabled (#2688)
- **taskList**: fix no task list not being displayed having no features (#2681)
- **frontend**: pass in entire project aoi extent for fgb filtering polylines #2663
- **frontend**: disable split by square for polylines
- **frontend**: disable splitting by square for line geom mapping #2663
- **backend**: use SecretStr for backend SMTP_PASSWORD
- **mapper**: bug with pagination on mapper summaries page
- add docstring for geom_type
- **xlsform**: update xlsx highway form to xls with latest form
- **frontend**: pass in entire project aoi extent for fgb filtering polylines #2663
- **frontend**: disable split by square for polylines
- **frontend**: disable splitting by square for line geom mapping #2663
- **backend**: use SecretStr for backend SMTP_PASSWORD
- **mapper**: bug with pagination on mapper summaries page
- **build**: issues from rebase

### Refactor

- **mapper**: replaced font-barlow with font-primary (#2700)
- **frontend**: remove old project creation code (#2705)
- missed console log
- missed console log
- **backend**: update code with json data models
- update test cases based on stub project creation workflow
- update test cases based on stub project creation workflow
- backend
- **backend**: simplify local dev odkcentral setup, no extra proxy rules, no https required
- backend
- **backend**: simplify local dev odkcentral setup, no extra proxy rules, no https required

## 2025.4.0 (2025-07-09)

### Feat

- **backend**: add highways xlsform for #2630
- **backend**: implement scheduled upload of project submissions to S3 (#2643)
- **backend**: add 'SENSITIVE' project and allow public access to public and invite only projects (#2653)
- **mapper**: display offline submissions in offline tab for debugging (+csv) (#2543)
- add status chip to project card & details section (#2623)
- Project Completed Workflow (#2618)
- **frontend**: request HOT's ODK server workflow (#2595)

### Fix

- **backend**: missing From header in smtp email send config
- **mapper**: display css overlay with locale warning in web-forms (#2665)
- **deps**: update dependency @electric-sql/pglite-sync to v0.3.7 (#2669)
- **deps**: update dependency @electric-sql/pglite to v0.3.4 (#2668)
- **deps**: update dependency @electric-sql/client to v1.0.5 (#2667)
- **backend**: add a check to get-form-media to avoid returning bytes
- **ci**: allow e2e workflow on forks (#2644)
- **frontend**: ensure 'include centroids' param included in osm exports (#2660)
- **backend**: update visibility logic for project access permissions (#2658)
- **frontend**: project qr option & submission table (#2657)
- **mapper**: prompt login before sending offline submission if made by logged out user (#2641)
- **mapper**: conditionally render status badges on project card (#2635)
- **mapper**: allow multiple submission id's tracked via entity property (#2634)
- **mapper**: add user_sub to api_submissions table via migration / login
- **backend**: submission count in project card and detail page (#2616)
- **mapper**: disable upload image preview (#2622)
- **backend**: suppress invalid error from pyodk about cache file  (#2614)
- **mapper**: mapping feature for a second time (#2601)
- **frontend**: submission count on project submissions page (#2612)

### Refactor

- **backend**: tweak SMTP vars for rollout dev/stage/prod, related #2458
- **backend**: update to latest pyodk, removing custom code, towards #2210
- update highways.xlsx --> highways.xls for consistency
- rename repo fmtm --> field-tm & update all links
- rename development branch --> dev
- improve the icon used for point data in both frontends (#2640)
- remove additional_feature entity functionality from fieldtm (#2633)
- add favicon.ico and favicon.svg in root to gitignore
- **userInvite**: invite multiple osm user by comma seperated value (#2621)
- **frontend**: user role access components (#2611)
- **frontend**: dedicated skeleton loader folder, reduce dup (#2609)

## 2025.3.1 (2025-06-17)

### Feat

- add status chip to project card & details section (#2623)
- Project Completed Workflow (#2618)
- **frontend**: request HOT's ODK server workflow (#2595)
- **backend**: update submission retrieval to use pyodk except in submission detail page (#2599)
- roadways mapping support
- **Backend**: Ensure form_id generated is returned
- **backend**: add project complete status to set it to read only (#2478)
- migration added to update osm_id type from int to bigint (#2552)

### Fix

- **backend**: submission count in project card and detail page (#2616)
- **mapper**: disable upload image preview (#2622)
- **backend**: suppress invalid error from pyodk about cache file  (#2614)
- **mapper**: mapping feature for a second time (#2601)
- **frontend**: submission count on project submissions page (#2612)
- **mapper**: allow creating entity even without login (#2607)
- **vectorLayer**: prevent stale FlatGeobuf response to be processed (#2605)
- **mapper**: pass xlocation to submission xml (#2600)
- **migration**: skip if no project found in odk central (#2597)
- **mapper**: task state update updating (#2593)
- **backend**: removed precommit changes in central schema
- **mapper**: submission_ids of the entity after submission (#2591)
- **mapper**: add domain to device id (#2592)
- **backend**: implement organisation approval request notification along with odk server request when applicable (#2589)
- **frontend**: user search 403 (#2587)
- **webforms**: add today to odk xml submission (#2585)
- **webforms**: tweak iframe height (#2583)
- **frontend**: organization creation related issues (#2580)
- **mapper**: use defined CSS var for entity status (#2579)
- ensure form_id generated is returned
- **mapper**: only load project summaries once (non-reactive)
- **backend**: hide odk xml from reading all projects response (verbose)
- **backend**: getting project if not logged in (mapper frontend)
- **mapper**: increase timeout downloading offline pmtile basemap
- **mapper**: add progress bar for offline basemap storage (user feedback)
- **mapper**: bigint handling in geojson properties, convert to string
- **frontend**: update URL validation logic (#2557)
- **mapper**: hide feature_exists question if mapping an existing entity #2430 (#2549)
- **mapper**: distorted loading spinner CSS on submit #2477 (#2548)
- **mapper**: clear old CacheStorage entries for webform scripts (#2547)
- **+page**: shift handle fetch project to effect block to reflect pagination (#2545)

### Refactor

- **userInvite**: invite multiple osm user by comma seperated value (#2621)
- **frontend**: user role access components (#2611)
- **frontend**: dedicated skeleton loader folder, reduce dup (#2609)
- **frontend**: project creation error handling (#2562)
- remove centra/form-xml endpoint (xml is in fieldtm db now)

## 2025.3.0 (2025-05-22)

### Feat

- **mapper**: fffline entity creation and webform submissions pt2 (#2525)
- **mapper**: offline entity creation and webform submissions sync when online (#2517)
- **mapper**: use geom javarosa format for xlocation (#2524)
- **mapper**: added deviceid to web form submission (#2519)
- **dependencies**: add markdown package with version >=3.8 to project dependencies (#2509)
- **backend**: SMTP email functionality and send invite emails to non OSM users (#2503)
- **mapper**: make project detail data available from local db fallback when offline (#2505)
- **mapper**: add offline banner notificiation + load project summaries from PGLite first (#2495)
- **mapper**: load fgb extract offline via opfs (#2502)
- **mapper**: added caching of odk web forms script (#2498)
- **mapper**: implement PGLite for local-first database in mapper frontend (#2427)

### Fix

- **update_xlsform**: auto add form settings configuration if not present (#2541)
- **mapper**: fix #2518 dbPromise loading order and spinners (better ux)
- **mapper**: partial fix for #2518, home page loading spinner
- **mapper**: selected entity geometry is a javarosa string by default
- **backend**: correctly handle exceptions on get form media method
- **mapper**: sending of offline submissions when connection restored #2530
- remove unecessary print from geomlog_to_entities migration
- **fetch**: clone the response stream so that it can be consumed again (#2523)
- satellite imagery zoom error & remove qr code tab (#2521)
- **mapper**: DbProject merge types, do upsert on getting project summaries (no delete)
- **mapper**: ensure web-forms.html is loaded from url root, not relative to project
- **backend**: correctly catch exception on failed Central s3 sync
- **frontend**: bulk user assign per project (#2501)
- **mapper**: build warning about SLTabGroup init
- **mapper**: add screenshot image for pwa manifest
- **mapper**: project specific ODK collect vs webforms config (#2492)
- **proxy**: disable the bunkerweb ui wizard to prevent unauthorized admin access
- **frontend**: show validation error if primary geom type not selected

### Refactor

- **mapper**: add offline tab back, load all submission photo file types (#2513)
- **backend**: minor tweak to integrations crud entity receive
- set enableWebforms frontend config var to default true
- **frontend**: Manage Organization & user roles  (#2367)
- **mapper**: task/entities color CSS vars & other fixes (#2482)
- **mapper**: skip polygon selection confirmation step (#2481)

### Perf

- tweak postgres max_connections and utilise pooling for performance
- **mapper**: attempt to slightly reduce memory spike on first project detail page load

## 2025.2.1 (2025-05-05)

### Feat

- **xlsform**: skip verification question if new feature (#2474)
- **frontend**: overlapping features selection via ui (#2451)
- **mapper**: display user-friendly translation names with corresponding country flags (#2469)
- **users**: add signin_type filter to user retrieval endpoints and allow org admin access (#2468)
- **backend**: add capability to create new users via api key (#2467)
- **backend**: add capability to create new users via api key
- **mapper**: resize image buttons for web form questions (#2452)
- **backend**: default organization settings and logo handling from env (#2441)
- **frontend**: add toggle to use odk collect during project creation

### Fix

- **mapper**: add font and move css over-ride to bottom of web-forms iframe body (#2473)
- **xlsform**: allow verification questions for every geom type (#2471)
- **mapper**: incorrect styling for buttons, backround color, spacing (#2460)
- **frontend**: error handling for invalid geojson data extract upload
- **backend**: remove user_roles join to avoid multiple projects result
- **frontend**: pass use_odk_collect through to validate-form endpoint

### Refactor

- **backend**: export FMTM_DB_URL as string directly from config
- minor refactors, remove print statements

## 2025.2.0 (2025-04-29)

### Feat

- **users**: add signin type filter to user list retrieval
- **mapper**: loading spinner when uploading form submission (#2445)
- **mapper**: default language warning v2 (#2432)
- **mapper**: auto-open web forms when entity created (#2429)
- **Details**: project visibility field add to edit project details (#2424)
- user invite functionality per project (#2391)
- **mapper**: add sidebar link to help translations via weblate
- **mapper**: allow configuration of sidebar items
- **mapper**: web forms image upload question improvements (#2413)
- **mapper**: allow users to revert mapped task to ready state (#2404)
- **backend**: allow verification group in form only if there are existing features in the project (#2396)
- project visibility implementation (#2400)
- **backend**: enhance user invitation process with user wise invite URL validation (#2399)
- **mapper**: allow override of using webforms (db var to force OdkCollect)
- generate data extracts based on the geom type (POINT, LINE, POLYGON) selected (#2382)
- **backend**: add user invites via URL functionality (#2378)
- **backend**: add api-key option to all endpoints (respecting auth and user roles) (#2376)
- **mapper**: make user login methods configurable via config.json
- **mapper**: added warmup latitude/longitude into form submission (#2372)
- **frontend**: comment tagging capability, searching list of available users (#2312)
- delete organisation only if no projects
- **mapper**: image file choice question image override by css (#2365)
- **backend**: form media retrieval route (#2354)
- **mapper**: Nepali language translations & fix more section blank contents issue (#2357)
- **backend**: role wise access to project summaries (public/private) (#2353)
- **backend**: allow for download of form media/attachments as list of URLs pt1 (#2348)
- **mapper**: cache form xml and ODK Web Forms js library across reloads (#2349)
- **mapper**: hide feature selection question in web forms (as it's prefilled) (#2347)
- **frontend**: define hashtags as lost of chips for better ux (#2344)
- add google login option to mapper frontend (#2331)
- **backend**: trigger s3 upload as soon as submission is made fixes #2339
- **mapper**: updated stepperLayout to true for webform (#2329)
- **mapper**: translations for all strings in the mapper app (#2328)
- **backend**: config to create projects with no existing geoms (new geom only) (#2278)
- **mapper**: load config from bundled S3, with default fallback (#2323)
- **mapper**: project summary page if no id specified (#2307)
- **frontend**: organization dashboard page (#2293)
- **mapper**: updates to web forms submission image upload (#2292)
- **backend**: add minimal query option for mapper frontend project summary (#2310)
- update the version of typescript client to 1.0.0-beta.5
- **beatend**: enpoint to list the organisation admins
- **backend**: add org id filter in project summary, calculate total subissions, mapped , bad and validated tasks
- **backend**: updated pytest related to changes made in backend
- **migration**: script to move existing raw data api fgb url to fmtm s3 bucket
- **backend**: return geojson url instead of fgb url, rename upload custom extract to upload data extract
- **migration**: script to move existing raw data api fgb url to fmtm s3 bucket
- **backend**: assign users to tasks (+ project team integration) (#2237)
- **backend**: add endpoint to upload form media such as images, videos, audio (#2275)
- **mapper**: draft web forms integration via feature flag (#2268)
- **mapper**: upgrade paraglide for nested translation fields, continue adding translations (#2258)
- **frontend**: dynamic styling and icons, loaded via config.json (#2255)
- **backend**: optimise generating project data (#2214)
- **frontend**: replace file upload button with drop zone (#2259)
- **mapper**: replace manager frontend PWA with mapper frontend PWA (#2247)
- **backend**: create separate user endpoints for different purposes (admin, org, project) (#2238)
- **project**: populate total task field after task creation (#2243)
- **frontend**: create new feature entities via API prior to ODK collect usage (#2156)

### Fix

- **organisation**: update get_organisation_admins permissions to allow authenticated users
- **frontend**: disable task splitting if no data extract included
- **mapper**: issue selecting existing feature (exception handling)
- **frontend**: logo sizing in primary app bar
- **frontend**: data extract issue on switching between project in mapper frontend (#2446)
- **backend**: role wise project visibility in mapper frontend (#2447)
- **mapper**: set translations via cookie instead of localStorage
- **mapper**: display confirmation dialog on task marked as completed (#2425)
- **mapper**: web form images not appearing (#2442)
- **mapper**: handle login redirect for user svcfmtm on invite (#2436)
- **backend**: calculate submission ids using instanceID (#2437)
- **mapper**: send correct entity status when submitting based on survey (#2428)
- **mapper**: add polyfills for missing browser functionality (#2422)
- **dialog-task-actions**: prettier fixes
- **frontend**: fixes #2416 for tiptap markdown render usage
- **osm-fieldwork**: if no verification fields, omit the survey group in xlsform
- **mapper**: missing translation for geometry confirm dialog
- **osm-fieldwork**: add the submission_ids field to the survey, with dummy values for now
- **frontend**: pass centroid param only if primary geom type is point
- **mapper**: calculate task centroid to display task lock icon on center (#2398)
- **mapper**: remove unecessary $derived from collect.ts (not svelte)
- **mapper**: avoid opening odk collect if web-forms enabled for new features
- **mapper**: broken web forms appearance / height (#2389)
- **mapper**: missed colon in css file causing prettier / pre-commit fail
- **mapper**: add xid and xlocation to web-forms submissions (#2385)
- **osm-fieldwork**: towards #2369, remove intro note, fix survey questions text
- **backend**: /users/usernames endpoint requires validator permission, not org manager
- **backend**: access to odk form media should be mapper permission
- **backend**: testing pre-signed ODK Central URLs during local dev
- **frontend**: raise error generated by backend
- **pre-commit**: raise exception with 'from' clause
- **mapper**: hide QR tab on webforms enable & fix geolocation prompt offscreen (#2364)
- **mapper**: minor UI fixes, confirm dialogue at top (#2356)
- **frontend**: replace user id with user sub id (#2345)
- **mapper**: web forms enable from config file (#2343)
- **mapper**: related to #2154, update entity status on webform submission
- **mapper**: fixes #2324 setting task index as submission task_id value
- **frontend**: accidental translation key addition to react frontend
- **migrations**: add foreign key constraint for project_team_users only if id column in user table exists (#2330)
- **backend**: allow mappers to create new entities
- **backend**: remove auth requirements from projects/search endpoint (allow loading home page without login)
- **mapper**: only load flatgeobuf layer if created at project creation (not empty project)
- **mapper**: update shoelace buttons to use variant for styling over classes
- **mapper**: allow for webform submissiosn without photo
- **projectDetails**: update hide/unhide tab & buttons logic (#2320)
- **frontend**: auth update after backend breaking changes (#2319)
- **version**: updated version of electric ts client to 1.0.0
- **deploy**: update the electric-sql version -> 1.0.0-beta.23
- **backend**: invalid sql when user id is passed due to early closure of sql ';'
- **backend**: add organisation id to avoid pydantic validation error
- **frontend**: align task lock icon within task area (#2301)
- **workflow**: skip backend smoke test
- Submission details page crashing when fetching photos fails (#2291)
- **workflow**: increase timeout of smoke test -> 120
- **backend**: remove un intended extra execute command
- **mapper**: usage of paraglide in web-form wrapper (languageTag deprecated)
- **backend**: pass null task id if feature lies outside task outline (#2277)
- **osm-fieldwork**: correctly get form_id string value during form update
- add missing findProject osm-fieldwork method back in
- **backend**: set osm_id property to negative value if it's not valid OSM (#2263)
- **frontend**: translations set on wrong frontend 😅
- **backend**: only replace S3 submission photo urls in local dev
- **frontend**: json serialise fgb --> geojson before upload
- **frontend**: project creation AOI area calculation correction (#2251)
- **migration**: add file to populate total tasks for old projects if null (#2246)

### Refactor

- **mapper**: restructure util functions
- **mapper**: hide basemaps & show info, instructions tab on webforms enable (#2423)
- rebrand from FMTM --> Field-TM pt1 (#2421)
- **mapper**: missed console log in mapper frontend
- move a few central related endpoints projects --> central router
- **frontend**: remove unused code on react frontend
- **backend**: move central validate-form endpoint to central router
- **frontend**: remove geolocation from manager frontend (expected on desktop)
- **backend**: add extra debug info if entity creation fails
- **backend**: move s3 bucket init to migration (run once) instead of api (replicas)
- **mapper**: use css files for all styles, with unocss transformer directives --at-apply (#2387)
- add translation using Weblate (French) (#2373)
- remove refs to __pypackages__ as no longer use pdm
- remove search api and use project summary api (#2332)
- **createProject**: refactor data extract handling process
- **frontend**: redesign project details page (#2264)
- **entitiy**: optimize entity lookup performance using Map for quick entity retrieval (#2287)
- make S3_xxx env vars mandatory for api startup
- **backend**: remove logic for fgb extract upload (handled on frontend)
- **frontend**: project details page component (#2261)
- **frontend**: entity creation workflow (#2252)
- **mapper**: remove task 'go to odk' button (#2250)

### Perf

- **backend**: improve performance of project status materialized view + other updates (#2408)
- **backend**: create materialized view of project stats for summary api (#2322)

## 2025.1.1 (2025-02-26)

### Feat

- separate out primary mapping geometry from new feature geometry (during proj create) (#2225)
- **frontend**: start user roles integration (#2207)
- **frontend**: task comments for individual features( #2218)
- **backend**: add task scheduler to backend services (cron jobs) (#2147)
- finalise S3 submission photos on backend + frontend (#2211)
- **backend**: replace custom ODK submission media upload with official external storage (S3) (#1894)
- **backend**: replace nominatim usage with pg-nearest-city reverse-geocode (#2199)
- **backend**: extract additional geoms into submission geojson featcol
- **frontend**: design modifications, project details, home page, header, buttons (#2148)
- **frontend**: show geometry label popups on submission details page (#2187)
- **frontend**: download split geojson during proj create (#2186)
- **frontend**: download filtered submissions, with option for geojson too (#2183)
- **backend**: endpoints to download form XML and create new form submissions (#2178)
- create script for generating project stats via API
- **frontend**: render points on both frontends, with colour determined by status (#2174)
- **submission**: add date range filter for geojson download (#2176)
- **mapper**: add i18n (internationalisation) frontend translations via paraglide js (#2155)
- **tasks**: add task to unlock tasks locked for over 3 days and reset entities after an hour (#1984)
- **backend**: return entity uuid on create (#2151)
- **backend**: add endpoint to create an entity in existing project for new geometry (#2145)
- **frontend**: update user roles list during project creation (#2135)
- **frontend**: add table component and manage users page (#2133)
- **backend**: add central-webhook service for triggering entity status updates in Field-TM database (#2130)
- **backend**: migration to add dataset property to old projects (#2126)
- **users**: add pagination and search functionality (#2124)
- **backend**: add endpoint to change global user roles (#2117)
- **frontend**: assign PM during project creation & refactor radix components (#2115)
- **backend**: warn users and delete user accounts after period of inactivity  (#2088)

### Fix

- **dialog-entities-actions**: update submission length check condition
- **backend**: set new_geom_type default to Polygon as temp fix for #2164
- **taskSelectionPopup**: update task popup task state label
- **submissionDetails**: display submission images on the submission field itself (#2216)
- add project create feature warning (10,000) and limit (30,000) (#2215)
- **frontend**: inconsistent task history names and styling (#2217)
- **backend**: update role to project admin to fetch user list (#2203)
- **frontend**: correctly include project name in geojson submission download file
- **frontend**: use fmtm-cursor-pointer for default user icon
- **frontend**: move new geom confirm dialog to center screen
- **extractGeojsonFromObject**: differentiate and visualize Polygon & LineString seperately (#2196)
- **frontend**: task lock logic, allow unlock by admins (#2188)
- **+page**: confirmation dialog close before redirection to ODK (#2185)
- **frontend**: add error message if project editing fails (permissions)
- **frontend**: add hot-tracking to react type declarations
- **backend**: TMS issues by using go-tilepacks and go-pmtiles (#2162)
- **backend**: support big int osm id fgb creation (#2160)
- **backend**: clear tiles from disk after generation (#2158)
- updated usage of shapestream requiring 'params' field
- **projectDetails**: update set odk credential logic (#2149)
- **frontend**: custom odk creds validation, relate to PR #2142
- **frontend**: allow users to select default odk credentials (#2142)
- **getTaskStatusStyle**: fix locked_for_mapping task state color
- **backend**: getting secret value from CENTRAL_WEBHOOK_API_KEY config var
- **frontend**: logic allowing for custom odk server creds during proj create (#2129)
- **frontend**: validated entity state visualization on map (#2122)
- **mapper**: flaky new feature polygon draw (#2118)

### Refactor

- **frontend**: replace old button with new button components (#2212)
- **frontend**: update link to custom ODK Collect --> v2024.3.5 (entity refresh on load)
- automatically determine geom type from javarosa geom structure
- remove sign out button from sidebar drawer
- replace two submission download endpoints with one
- tweak odk tunnel testing config button
- **frontend**: remove task_filter field from frontend intent url
- **frontend**: simplify SetSnackBar action with defaults (#2192)
- use @types/react for custom module declarations
- ensure translations match
- move unused root level 'images' to prototyping docs section
- **submissionDetails**: fix bracket, don't show new_feature geometry object (#2121)

## 2025.1.0 (2025-01-24)

### Feat

- **backend**: add `integrations` router with API key functionality (external apps) (#2110)
- entity pulse effect on rejected submissions (#2018)
- **mapper**: distance constraint add on frontend (#2084)
- **frontend**: submission table date range filter (#2091)
- **backend**: get api for project's geometry log (#2090)
- capability to draw new polygon and linestring geoms (#2082)
- **backend**: add filters for submission date in submission table and downloads (#2077)
- **backend**: osm-fieldwork --> 0.18.0 (submission filter param + config new feat geom type)
- **geolocation**: comments add
- add submission ids in entities statuses endpoint (#2038)
- consider every additional entities without clipping them with AOI (#2017)
- update the version of osm-fieldwork (#2029)
- **backend**: send org approval message to creator (#2008)
- add submission ids as a dataset property for the entities (#2007)
- update the version of fmtm-splitter 2.0.0 (#1996)
- **mapper**: project details section add to bottom sheet (#1994)
- **mapper**: prompt user to download custom ODK Collect on first load (#1989)

### Fix

- **backend**: delete submission photos while deleting project to avoid foreignkey constraint (#2112)
- **backend**: review state for received on submission table (#2101)
- **+page**: remove irrelevant subscribeToEntityStatusUpdates call in onMount
- use task index instead of id in task boundary geojson properties (#2095)
- **mapper**: get entities after page load to speed up first paint (#2051)
- **backend**: get total_tasks count on single project response
- **backend**: various fixes based on sentry error reports (#2053)
- default odk creds when organisation do not have their own during project creation (#2070)
- change geom to geojson in db model
- **generateBasemap**: update tile source option value (#2050)
- **geolocation**: fetch routing api on every 10 seconds
- **dialog-entities-actions**: show alert instead of turning on location on navigation
- **createProjecSlice**: clear additionalFeatureGeojson state after successful project creation (#2041)
- compose file name for backend test stage
- **mapper**: replace task id with index on activities panel (#2002)
- **mapper**: task id with task index on mapper frontend  (#1997)
- **backend**: include organisation name in minimal project query results (#1993)
- **frontend**: small fix to reset frontend login if cookie refresh fails
- **mapper**: offline mode button visibility & basemap component TS type error (#1990)
- parse geojson to featcol in generate data extract (#1983)

### Refactor

- **mapper**: feature legend & layer-switcher (#2107)
- **mapper**: relocate entity sync button (#2100)
- **frontend**: organization management pages (#2097)
- **frontend**: JS to TS conversion: update useDispatch to useAppDispatch  (#2076)
- **frontend**: update TS types on actions (#2054)
- replace incorrect osm libya logo with official osm logo
- **frontend**: terminologies and wording update for users (#1978)
- **mapper**: ts errors on frontend (#2006)
- **mapper**: add mapping guide to sidebar + update links

## 2024.5.0 (2024-12-11)

### Feat

- update auth cookie logic for both backend and frontend (#1974)
- **mapper**: add navigation mode to map (pitch angle / rotate) (#1973)
- **debug**: add cloudflare tunnel config to simple configurable frontend button
- **frontend**: add 'Start Mapping' call to action button on homepage cards (#1968)
- **mapper**: add new point geom in maplibre terradraw, inject to ODK collect (#1966)
- **projects**: add organisation_logo field to ProjectSummary model (#1956)
- **mapper**: add zoom to extent button to map (#1947)
- **frontend**: all uploaded submission features/geometries on submission instance page (#1931)
- **mapper**: frontend pmtile basemap management pt2 (#1925)
- **mapper**: set entity (feature) color based on it's mapping status (#1921)
- **mapper**: basemap control component + opfs pmtile support (pt1) (#1922)
- **mapper**: frontend login + remove temp auth from React frontend (#1903)
- **splitTasks**: additional entities feature count add to split tasks section (#1906)
- **mapper**: basemap layer switcher integration for maplibre (#1835)
- **submission**: add project_contributors dependency for permission … (#1873)
- **splitTasks**: add total number of features on split tasks section (#1880)
- **mapper**: map new feature in odk btn (#1879)
- **frontend**: visualise submission photos via slider (#1857)
- **backend**: API to delete user account #1661 (#1848)
- **mapper**: start improved mapper flow (#1854)
- **mapper**: flatgeobuf maplibre component for loading features (#1851)
- update API to use events and task states + fixes to backend refactor (#1838)
- **backend**: remove SQLAlchemy and replace with async psycopg db driver (#1834)
- **frontend**: mapper UI frontend refactor (#1830)
- **frontend**: mapper frontend continuation (#1823)
- mapper frontend using ElectricSQL ShapeStream (live updates) (#1760)

### Fix

- **auth**: final fixes to temp/osm auth across frontends
- finalise auth setup between frontends (#1981)
- **backend**: correctly return JSONResponse content on refresh endpoints
- apply pagination after fetch submissions from odk (#1971)
- **mapper**: remove extra semicolon from new_feature odk field injection
- **mapper**: correctly inject username into qrcode from logged in details
- **frontend**: update token refresh calls to match updates in PR #1948
- **backend**: ambiguous project_id reference in project summaries .all()
- **frontend**: update min height of project home page card, move start mapping button
- **backend**: including num_contribotors and total_tasks to the project response
- **frontend**: default do not show map on home page
- **mapper**: attempt fixing missing basemap download buttons on mobile
- **backend**: login enforced for management, additional temp login option for mappers (#1948)
- **+page**: remove user details from localStorage in case of session expiration (#1965)
- **backend**: polygon geometries; remove holes, fix right hand rule (#1961)
- Submission Instance Page, Create Project (#1958)
- odk credentials are passed without encrypting at first to avoid double encryption (#1957)
- **mapper**: better distinguish create project layer colours (#1936)
- **frontend**: remove trailing slash from activity endpoint (#1932)
- **backend**: use pydantic SecretStr for all sensitive env vars
- edit multi additional entities names replacing space with '_' (#1926)
- **backend**: resolve route ambiguity for /tasks/activity endpoint (#1924)
- **frontend**: update the body of generate-project-data;parse null as a json instead of form data (#1919)
- **mapper**: geolocation layerswitch bug (#1914)
- **mapper**: frontend enhancements, add more instructions (#1905)
- **mapper**: mobile broser map control placement fix (#1899)
- **project**: allow users to view project cards without login (#1902)
- **frontend**: project creation wording form --> survey (#1858)
- **frontend**: minor fixes including bottom sheet drag up (#1895)
- trailing slashes from endpoints, fix check_access for backend roles (#1893)
- **backend**: update check_access logic to allow checking for org_manager to a project (#1892)
- **backend**: create and delete organisation (#1867)
- **backend**: fix permissions for backend project routes (#1885)
- **backend**: building of extra cors origins, type mismatch
- **backend**: update project xlsform SQL after backend refactor (#1872)
- **mapper**: disable mobile browsers to pull-to-refresh functionality (#1878)
- **mapper**: loading of electric shapestreams, api call ordering
- **backend**: cors origin list building when DEBUG not set on localhost
- **mapper**: task comment events for mapper frontend (#1871)
- **backend**: remove auth bypass in for HOTOSM org #1785 (#1845)
- **formUpdateTab**: xFormId undefined issue fix on form update (#1863)
- **createProjectService**: replace all spaces with underscore (#1862)
- **frontend**: pass additional entity file name to backend (#1860)
- **additional-entity**: allow custom properties to create entities list (#1861)
- **backend**: s3 upload and db insertion for submission photos (#1856)
- **frontend**: after backend refactoring to events (#1844)
- mapper frontend task display and event POSTs (#1842)
- add temp ?sslmode=disable to electric url due to electric#1792
- **backend**: allow empty task id in entity statuses for new geopoint (#1822)
- dockerfile warning such as Casing and whitespace separator
- updated osm-fieldwork -> 0.16.8 (#1814)
- **files**: cleanup function remove
- **QrcodeComponent**: reduce qrcode skeleton size
- **dialogTaskActions**: add task id filter on odk redirect
- **qrcode**: increase qrcode size
- **createProject**: xlsform key update, fix customForm upload issue
- **editor**: solve editor empty issue on manageProject on initial render
- **submissionsTable**: on filter reset, set task_id to null

### Refactor

- **mapper**: improve logic for rendering basemap action buttons
- **logging**: enhance error logging with stack information across multiple modules (#1887)
- **mapper**: upgrade mapper frontend to Svelte 5 Runes (#1846)
- remove unnecessary db injection where not needed
- update link to custom ODK build (renamed to -FMTM)

## 2024.4.1 (2024-10-24)

### Fix

- **backend**: allow empty task id in entity statuses for new geopoint (#1822)
- dockerfile warning such as Casing and whitespace separator (#1815)
- updated osm-fieldwork -> 0.16.8 (#1814)
- **files**: cleanup function remove
- **QrcodeComponent**: reduce qrcode skeleton size
- **e2e**: comment out test until CI fixed
- **dialogTaskActions**: add task id filter on odk redirect
- **qrcode**: increase qrcode size
- **createProject**: xlsform key update, fix customForm upload issue
- **editor**: solve editor empty issue on manageProject on initial render
- **submissionsTable**: on filter reset, set task_id to null
- **backend**: pyxform usage only allowing xls file extension (#1758)
- **backend**: pyxform usage only allowing xls file extension (#1758)
- **map**: set default baseLayer to OSM (#1600)

### Refactor

- update link to custom ODK build (renamed to -FMTM)
- update link to custom ODK build (renamed to -FMTM)
- update link to custom odk collect signed 2024.2.0
- update link to custom odk collect signed 2024.2.0

## 2024.4.0 (2024-09-24)

### Feat

- **frontend**: allow selection of additional features during project creation (#1806)
- **backend**: endpoint to create additional Entity lists on a project (#1799)
- **backend**: endpoint to retreive submission photos (#1794)
- **backend**: use XLSForm injection during project creation (#1792)
- **submissionDetails**: if new feature point add then zoom to the point (#1797)
- **projectDetailsForm**: tms url description text add (#1795)
- update form by injecting mandatory fields and validate it (#1763)
- **frontend**: project not found page (#1768)
- mark tasks validated + start conflation UI (#1743)
- add project not found page (#1762)
- **backend**: capability to send messages to OSM users (notified via email) (#1747)
- **backend**: ODK submission user photos to S3 for easy access (#1744)
- **frontend**: add Playwright test for project creation workflow (#1700)

### Fix

- updating form, with disclaimer to use original form
- **frontend**: only call additional-feature API if one is set by user
- **backend**: submission route ordering causing 500 error
- **backend**: error handling if submission download fails
- **backend**: add DEBUG override to /refresh for tunnel testing
- **files**: add pname, odkToken, osmUser as dependency (#1796)
- **backend**: use latest pyxform syntax for xlsform conversion (fix xls ext usage) (#1789)
- **frontend**: correct text in validation table to show the marked as validated (#1777)
- **backend**: allow empty task id and osm id for new geopoint (#1774)
- **frontend**: map ui alignment on various devices (#1772)
- **createProject**: lineString validation remove (#1767)
- **backend**: pyxform usage only allowing xls file extension (#1758)
- remove id from the conflated geojson (#1735)
- **updateReviewStatusModal**: remove error display & disable btn if no status selected (#1728)

### Refactor

- **frontend**: do not use debug=true flag on form validation
- **backend**: remove task_id and task_filter params from XLSForm (#1805)
- **backend**: remove xforms table from database, refactor project creation (#1804)
- **frontend**: move QR code & improve base map layer selection component (#1788)
- **backend**: rename public beta org to `hotosm` (#1784)
- update link to custom odk collect v2024.2.4 download
- update link to custom odk collect signed 2024.2.0
- **frontend**: ui padding tweak & enhancements (#1750)
- **backend**: correct username of contributors  (#1751)
- **frontend**: rename data extract file download (project id + 'map features')
- **frontend**: further upgrades from JavaScript to TypeScript (#1746)
- **frontend**: additional upgrades javascript --> typescript (#1737)
- reword Data Extract --> Map Features  (#1736)
- remove usage of sqlalchemy-utils (db init done by sql script)

## 2024.3.2 (2024-07-31)

### Feat

- **backend**: delete s3 objects on project deletion (#1718)
- **backend**: updated generate_project_files to bulk upload entities (#1714)
- **frontend**: working submission comments to submission page  (#1709)
- **backend**: calculate overlap percentage for the conflation (#1687)
- **frontend**: add user to task popup (#1670)
- **backend**: add helper route to convert multipolygon geojson --> polygons
- **backend**: update split-by-square to avoid creating tasks with no features in it (#1642)
- **backend**: endpoint to conflate the submission with osm data (#1594)
- implement global jwt token authentication for login (#1574)
- add new endpoint to refresh the app user token (#1583)

### Fix

- **frontend**: increase maxZoom if project details map 20 --> 22 (drone imagery)
- xlsform question ordering + pmtile generation when custom TMS (#1721)
- **frontend**: submission map chloropeth updating (#1716)
- **uploadArea**: allow to reset polygon even if its a geojson file on draw option selection (#1713)
- **projectTaskStatus**: dialog task_status text update on task update (#1712)
- **backend**: remove option for updating form category type
- **frontend**: disable form category updates (#1704)
- **backend**: generating project files passing project id to background task (#1708)
- **project**: display error generated on the backend (#1693)
- **frontend**: button click feedback on form update (#1692)
- **frontend**: reduce task overlay opacity (#1682)
- increased expiry of access token to 1 day (#1672)
- **manageProject**: hide user tab until its api integration (#1669)
- **backend**: ensure log level name is used (not Level 10, etc)
- **backend**: ProjectUserDict usage and standardise geojson parsing/usage throughout (#1659)
- **backend**: better handle invalid multipolygon geoms
- **backend**: allow multipolygons to choose as task area (#1645)
- **backend**: add hashtag to #domain-project_id during proj create
- **createNewProject**: save current form step state on previous btn click (#1643)
- **selectForm**: update select category description (#1644)
- **frontend**: display submission point feature if feature not in extract  (#1638)
- **frontend**: avoid map legend overlay on small screens (dynamic size) (#1637)
- prevent project generation if api failure (#1627)
- replace lru_cache with async for getting odk creds
- **backend**: addded created date on the project response, set expiry of access token to 1 hour (#1633)
- **hotfix**: download of basemaps in ui, max zoom level 22 used for tms
- **backend**: add INVALIDATED status option back in (#1618)
- **featureSelectionPopup**: allow any users to map feature (#1612)
- **backend**: parsing of hashtags (allow separation by comma, space, or semicolon) (#1607)
- **enums**: uncomment previous get_action_for_status_change code (#1609)
- **map**: set default baseLayer to OSM (#1600)

### Refactor

- **backend**: remove additional warning logs from check_crs function
- **backend**: improve error message if no project submissions present (#1696)
- **backend**: simplify logic for EXTRA_CORS_ORIGINS validation
- run latest pre-commit hooks
- run pyupgrade pre-commit hook
- **frontend**: simplify infographics API usage (reuse Entities data) (#1601)
- return access_token response to browser (in memory only)
- access_token expiry --> 1hr, refresh_token expiry --> 7 days
- remove redundant logic for refresh token func
- use pydantic model_dump over .json method
- replace RS256 jwt signing with simpler HS384 (#1622)
- fix refs to project_admin --> project_manager after PR merge
- **frontend**: update remaining JavaScript files to TypeScript (#1602)

## 2024.3.1 (2024-06-24)

### Feat

- add healthcare form category & minor fixes (#1555)
- use Matomo tracking web component, with accept/disagree prompt (#1546)
- **frontend**: upgrade React v17 --> v18 (#1542)

### Fix

- **submissionDetails**: retrieve task_id directly from submissionDetails (#1595)
- **frontend**: set submission table task_id from submission task_id
- ensure task_id field is always included with submissions (#1589)
- **frontend**: replace getting task_id from submission with url param
- ensure `status` Entity field is updated alongside survey form `status` field (#1586)
- **createProject**: disable submit btn until redirection to details page (#1585)
- **customTable**: misalignment via classname add (#1578)
- **frontend**: recharts UI misalignment (#1575)
- **taskSubmissions**: show task card of tasks even if no features, view submissions btn hide if no features (#1571)
- **charts**: size state to track responsive container to fix charts misalignment (#1570)
- **projectDetailsV2**: taskLayer color not update issue solve (#1569)
- **frontend**: block project create if no extract features (#1561)
- **frontend**: redirect user to requested page after login (#1559)
- **frontend**: only display matomo tracking banner in prod
- **frontend**: do not display pmtiles generated for another project
- **frontend**: add tile format to basemaps table, only show cache icon if pmtile
- **backend**: loading entity by intent using uuid xformid (#1538)
- **frontend**: correctly invoke matomo & sentry tracking in prod

### Refactor

- **frontend**: update links for odk collect by intent task_id --> task_filter
- **frontend**: update download url for custom ODK Collect APK
- **frontend**: update link to custom odk collect from intent apk
- **frontend**: import hotosm/ui styles.css --> style.css change
- remove reference to 'topo' basemap imagery provider (usgs)
- rename fmtm.dev --> docs.field.hotosm.org for docs site

## 2024.3.0 (2024-05-28)

### Feat

- add link for interactive xlsform editing during project creation (#1480)
- update PWA config with 2023 icon requirements and caching (#1474)
- download submissions in geojson (#1517)
- add OpenTelemetry configuration for backend API (monitoring) (#1496)
- prompt user if task area is not fully mapped on mark complete  (#1493)
- use task index as an user facing task_id (#1470)
- **frontend**: login options to frontend, OSM or temp auth (#1458)
- frontend buttons to load Entities in ODK Collect by intent (#1449)
- distinguish between tasks locked by the current user and tasks locked by others (#1469)
- append extra hashtag to projects with domain and project id identifier (#1454)
- endpoints for getting Entity data & updating Entity mapping status (#1445)
- temporary authentication login for mappers (svcfmtm) (#1410)
- add /projects/features endpoint for project FeatureCollection (disaster.ninja integration) (#1442)
- Playwright integration with test cases to be written (#1433)
- implement ODK Entities for project creation (#1383)

### Fix

- lock map feature if 'Map Feature In ODK' clicked (#1516)
- pmtile basemap generation and remove temp workarounds (#1535)
- **backend**: generate location_str in model_validator instead of computed_field (#1534)
- **backend**: validation_exception_handler pass all required params
- valid matomo tracking script
- pass project aoi as a outline geojson (#1533)
- typo error in project name prefix in submission-download-geojson (#1523)
- download submissions(csv,json) & refactor submission endpoints (#1519)
- populate task_id correctly in feature properties (#1515)
- refactored project dashboard and submission graph (#1509)
- **dialogTaskActions**: same name variable conflict solve (#1506)
- **backend**: use task ids to count validated and mapped status (#1485)
- **backend**: get contributors count in project summary (#1484)
- task hover popup & disable splitting algo without linestring (#1481)
- login methods after temp cookie auth (#1471)
- **frontend**: do not call introspect endpoint on /osmauth callback
- basemap tile download, refactor to use /{project_id}/name (#1467)
- **frontend**: invalidate login if mismatch between existing and new user login (#1462)
- role mapper to login required in data extract (#1450)
- fix list-forms endpoint logic to return list of dicts
- activity comment api calls in frontend (#1435)
- handle multipolygon geometries for project area (#1430)
- XLSForm template download endpoint for specified categories (#1441)
- filter task_history endpoint using task_id (#1436)
- update logic for more flexible submission json --> geojson
- add optional auth to raw-data-api calls, plus folder structure for persistence (#1431)
- project details mobile UI, user details in header (#1407)
- **backend**: allow missing odk_token for project, but log warning
- add odk_token from projectInfo to qrcode creation
- project name editing validation (#1416)
- return proper error message if form edit is invalid (#1415)
- default UNDERPASS_API_URL no trailing slash
- more informative browser tab titles/details (#1411)
- update task activity endpoint (#1406)
- project edit form update validation (#1397)

### Refactor

- remove missed warning log from update_survey_form
- remove broken submission code no longer used
- use HTTPStatus enum for helper route response codes
- fix ambiguous typos preventing pre-commit codespell passing
- run codespell spelling fixer
- replace unecessary outline_centroid for tasks with ol.extent.getCenter (#1447)
- merged multi polygon to single polygon (#1426)
- task comment response and schema (#1423)
- response of update task status and added user info in task history (#1419)

## 2024.2.0 (2024-04-03)

### Feat

- OPFS-based offline-first PMTile basemaps (#1395)
- endpoint to check the validity of login cookie (#1380)
- add link to custom ODK Collect build in sidebar menu
- toggleable debug console on mobile in local/dev/stage (#1371)
- handle geo orientation crash firefox & safari (#1381)
- raw sql replacing sqlalchemy in auth/me endpoint (#1334)
- added marker blue dot
- navigation icon changes
- uploadArea edit AOI btn add (#1346)
- navigation WIP
- submission review status modal (#1246)

### Fix

- default UNDERPASS_API_URL no trailing slash
- post message added undefined check
- vite test
- hotfix add top level id to geojson with it missing
- replace custom pyxform with multi-stage bytesio usage
- hotfix add top level id to geojson with it missing
- reduce length of random id generated for data extract
- fix random integer generation if missing in data extract
- update user profile image (#1373)
- log event for sensor
- ui for basemap gen, tooltip titles (#1363)
- blank space input validation (#1362)
- issues on project summaries with no centroids
- remove add org btn, redirect for submissions page (#1332)
- **hotfix**: use centroids for extract division by task area (#1336)
- return db user instead of auth user on /auth/me (#1247)
- reduce length of random id generated for data extract
- fix random integer generation if missing in data extract
- **hotfix**: use centroids for extract division by task area (#1336)
- default UNDERPASS_API_URL no trailing slash
- hotfix add top level id to geojson with it missing
- reduce length of random id generated for data extract
- fix random integer generation if missing in data extract
- **hotfix**: use centroids for extract division by task area (#1336)
- **hotfix**: use centroids for extract division by task area

### Refactor

- separate response for comment and task status history (#1391)
- update submission in s3 even if reviewstate is updated (#1379)
- updated the version of fmtm-splitter -> 1.2.1 (#1375)

## 2024.1.0 (2024-03-05)

### Feat

- add rich text editor project creation instructions field (#1311)
- add task_deps to get xform_name for a task
- add simple ui to delete projects on frontend (#1314)
- add helpers router to helper util endpoints
- cookie check added for auth check
- improve form validation logic, allow xform xml uploads (#1294)
- implement opening the generate tiles modal when download in qr is clicked
- replace local `useState` for generating mb tile modal with global state
- add global state for `toggleGenerateMbTiles` modal and add types for it
- add mbtiles btn back in, pie chart progress (#1278)
- add helper route to convert fgb --> geojson
- add map popups to data extract geometries (#1266)
- **manage-organisations**: implement skeleton loader while Organizations are being fetched
- **manage-organizations**: add `OrganizationCardSkeleton` component
- flatgeobuf data extracts on frontend & backend (#1241)
- added bbox in read project's outline (#1244)
- added approved in get organisation response (#1226)
- improve submissions dynamic filtering (#1217)
- api returning details of unapproved org (#1218)
- filters on submission table (#1191)
- init public beta org and svcfmtm user migration (#1206)
- endpoints for task comments (#1171)
- add community_type for organisations, add unapproved org list endpoint (#1197)
- osm-rawdata for generating data extracts (#1183)
- create / edit organization form (#1178)
- **frontend**: default organisation credentials during proj create  (#1174)
- task history end point with associated user (#1071)
- manage / edit project UI (#1154)
- mapper role (#1163)
- project admin role (#1133)
- **frontend**: project deletion capability
- set project delete endpoint to org_admin only
- project submissions page (#1150)
- dynamic qrcode generation via frontend (#1143)
- add AOI editing to map during project creation (#1135)
- endpoint to return count of validated and mapped tasks (#1138)
- added withcredential to include cookies on organization list api
- paginated submissions per task (#1128)
- organisation approval and admin endpoints (#1126)
- add test coverage metric (#1129)
- paginated submissions by project (#1110)
- add basic user role support to backend (#1094)
- cookie based authentication (#1091)
- use flatgeobuf data extracts (#1047)
- **backend**: form fields for the submision table (#1072)
- new project details page (#1070)
- get contributors by project (#1062)
- endpoint for submission page count by date (#1051)
- **backend**: project dashboard endpoint (#1054)
- cache submissions in s3 (#1035)
- add mamoto tracking to prod frontend (#1040)
- integrate fmtm-splitter and remove splitting code in fmtm (#1037)
- project info legend (#1017)
- add profiler to calculate route execution time (#1020)
- capacitor geolocation and orientation (#1016)
- cluster spread on click (#1007)
- **frontend**: edit draw AOI in create project (#999)
- generic endpoint to get task status from db

### Fix

- update osm-fieldwork --> 0.5.3 for validateMedia fix
- submission detail of each task's submission (#1324)
- **frontend**: project details improve UI responsiveness (#1321)
- redirect to loginPopup on Manage Organization click if user not signed in (#1322)
- **backend**: format of task_id in xform_name for getting submissions
- **frontend**: decrease generate-log interval 2s --> 5s (server load)
- **backend**: only access db once during task creation
- **backend**: do not overwrite form_category with form filename
- **backend**: update form endpoint updates xform_category (not xform_title)
- **backend**: generate project-log based on odk_token in tasks
- **backend**: add xform_category during project creation
- **frontend**: automatically use default odk org creds if present
- use defusedxml for xml parsing, only parse one in proj creation (#1316)
- **frontend**: revert change to ProtectedRoute attempting cookie access
- **frontend**: remove 'use client' react/nextjs delcarations from files
- **backend**: run xform update in background task
- **backend**: bug with xform/xlsform reading with suffix appended
- **frontend**: update odk collect qrcode task id in metadata_phonenumber
- update-form endpoint working
- **frontend**: form update page UI + correct post params
- update project_admin role to return user/project dict
- fix form validation check during project creation
- fix form naming during creation, media upload, appuser set
- update xform name to fetch submissions (#1306)
- remove data extract upload type (#1261)
- **frontend**: only load my organisations once on tab click (#1287)
- **frontend**: hotfix allow access to project details without login (for qr codes)
- fix xform name in task feature count dict
- check for existing project name (#1285)
- **frontend**: hotfix allow access to project details without login (for qr codes)
- fix xform name in task feature count dict
- updated the xform in form fields
- **frontend**: hotfix disable aoi area check temp
- **frontend**: hotfix allow access to project details without login (for qr codes)
- xform name in task feature count dict (#1288)
- default map background changed to white (#1281)
- cast osm_id as string for geojson id
- top level id in geojson Feature as osm_id
- create odk projects with prepended 'Field-TM xxx' to identify
- **frontend**: update qrcode form_update_mode --> match_exactly for sync
- double wrapped db.execute statement in text()
- fix passing project id for odk creds proj deletion
- wrap raw sql expressions in SQLAlchemy.text
- update odk_central_url validation to prevent blank string
- extra logs when extracting odk creds from proj/org
- put feature id on top level of task geojson for odk collect
- update logic getting default org odk creds
- geojson task splitting props in odk collect format
- logic to bypass project_admin if public beta
- update public org checking logic as part of role check
- allow public project creation during public beta (#1274)
- set sqlalchemy connection max_overflow unlimited, until task queue
- **frontend**: change console log msg check to type check
- reduce db connections during project creation
- **frontend**: console errors when msg prop is not defined
- **frontend**: handle case when console error is not string
- temporarily bundle minio in prod until minio instance profile
- make data_extract_url optional for ReadProject schema
- data extract splitting by task refined, update download endpoint (#1269)
- console log errors during project creation
- qrcode download from task popup
- rendering of qrcode based on task_status
- task splitting with custom data extract (#1255)
- dynamic submissions legend chloropeth (#1250)
- update initial_feature_count --> feature_count and populate values (#1265)
- use raw sql for organisation crud (#1253)
- file validity check on fileUpload only once (#1262)
- send bbox from geojson properties to josm (#1256)
- comment broken SubmissionMap import on frontend
- move OdkDecrypted logic into project_deps (#1239)
- qr popup on task status & styling (#1184)
- add created_by user id to organisation table (#1232)
- project org UI issues (#1230)
- required odk credentials if no organisation default (#1205)
- removed deps from delele org api (#1233)
- update schema to edit only required fields (#1223)
- first coordinate check when check_crs geojson
- data extract generation and task splitting with polylines (#1219)
- update task status when mapping starts (#1208)
- org creation using Form params
- add odk_central_url to org details returned
- project creation workflow fixes (task splitting) (#1194)
- axios interceptor testing
- feature type not being saved as a geojson type
- axios interceptors fixing test
- project submission card UI enhancement (#1186)
- update db relations for generating submissions (#1179)
- remove approved flag from organisations endpoint
- organisation routes role usage & approval
- baselayer url changed with token
- create popup outside of async request (fix ios login) (#1167)
- organisation logo display full width (#1166)
- map default odk credentials to organisations (#1123)
- **backend**: append /v1/ to odk_token url for qrcodes
- **frontend**: remove svcfmtm from loginSlice initialState
- zlib compress dynamic QR codes from frontend (#1159)
- project submission date and time formatted (#1160)
- project creation draw and max boundary area (#1157)
- **frontend**: do not render qrcode if odktoken is empty
- API interceptor used in getOrganizationRequest
- login_required decorator return value converted to AuthUser
- all usage of AuthUser replace .get methods (#1142)
- use optional params for extra AuthUser items
- Depends usage for task_submissions endpoint
- tile archive download for projects
- use organization_manager table for org admins
- limit project area during create (#1109)
- editable vector layer in ol for project creation (#1102)
- task split by square fail if data extract pending (#1095)
- optimize the performance of project dashboard (#1079)
- create & edit project UI fixes (#1078)
- more robust method to support different date format
- string based date to custom date format for over 7days
- add image to user profile (#1053)
- homepage height, split on square disable button (#1046)
- authentication on delete projects api (#1042)
- **frontend**: use task status string directly (#1032)
- prevent generate building task without int (#1030)
- serialize task status as string (#1031)
- retriving field value directly using model object
- task status var type, openlayers styling (#1026)
- allow qr code access from all users (#1023)
- error while using task splitting algorithm when drawing aoi
- use async by default, with occasional def threading (#1015)
- changed post request to get
- add template data extract example (#1011)
- improve logging if organization patch fails
- setting S3_DOWNLOAD_ROOT if not debug
- set S3_DOWNLOAD_ROOT if empty string
- correctly set org logo url on update
- upload organisation logo in S3 (distributed) (#1008)
- **frontend**: project summary search all (#1005)
- post task split type, dimension, num buildings (#1003)
- solve pagination error (#997)
- revert FastAPI UploadFile.getvalue(), use .read()
- **frontend**: custom tms url input (#998)
- rename upload-->project_geojson upload boundary
- add_obj_to_bucket s3 method all args
- use S3_DOWNLOAD_ROOT for s3 downloads
- project.project_info as a dict, not list
- set uselist=False for Project-->ProjectInfo relationship
- get_form_full_details func not a json
- refs BETAProjectUpload --> ProjectUpload
- use sync def for non-io bound tasks
- minor fixes, project_info dict, utils bg tasks
- add uuid in read project and total_task in generate-log (#978)
- add task_split_type to project when task splitting complete (#990)
- sign in text, user profile (#996)
- task id on task polygon and feature extracts (#976)
- create new project aoi zoom (#989)
- **install-script**: add DOCKER_HOST to top of bashrc
- enforce https for osm oauth callbacks
- add is_public option to s3 bucket init

### Refactor

- use pyxform fork for BytesIO XForm usage (#1327)
- **frontend**: round creation progress to nearest percent
- **backend**: add log after project xform update complete
- remove projects.xform_title completely, in favour of xform_category
- usage of form_category variable --> xform_title --> xform_name
- remove redundant central endpoints
- reduce API calls on home page and project details page (#1315)
- remove verbose logs from task pydantic model
- **backend**: remove verbose logs on project home page
- **backend**: remove project boundary upload endpoint (not used)
- remove categories from form list, update to raw sql
- old organization creation page removed (#1299)
- add ts types to store (#1286)
- remove unneccessary consoles
- update logic for odk form creation & media upload
- correctly set project.project_name_prefix on creation
- remove code for manual service worker registration
- update sentry to only run on prod website
- removing redundant code for removing extra closing </osm> tag (#1264)
- reorganize the code to make it cleaner
- changed sync to async gather_all_submission_csvs (#1258)
- improve flatgeobuf loading and generation (#1235)
- remove old edit-project code (#1210)
- org creation page consent questions (#1185)
- task status update endpoint to adjust mapper role (#1180)
- cast all fields for sqlalchemy with python types (#1173)
- add extra error handling if data extract download fails (#1158)
- remove withCredentials from org endpoint (use interceptor)
- **frontend**: use absolute (aliased) imports over relative imports (#1136)
- fix return type for organisation url validator
- update project dashboard to use deps functions (#1127)
- add metadata_username to odk qr code as test
- refactor odk appuser + qrcode function naming
- fix linting errors in project_crud
- renaming for consistency with database (#1114)
- remove variable from docker install script
- fix all pre-commit.ci linting errors (#1101)
- organization routes/crud/schemas to use best practice (#1096)
- replace project last active validator --> serializer
- task status fetched from enums (#1082)
- serialization for task_status and created project dashboard fields (#1076)
- pydantic v2 deprecations (#1074)
- rename mamoto --> matomo
- replace get_user_by_id with get_user on login
- remove /images/ endpoint, replaced by s3 logos (#1013)
- remove endpoints specific to janakpur project (#1012)
- use DEBUG param to determine S3_DOWNLOAD_ROOT local
- bytesio .seek(0) & .read() methods with .getvalue() (#1001)
- replace deprecated on_event with lifespan event
- generate uuid for background tasks automatically
- make get_odk_project_full_details synchronous
- rename project route variables for clarity
- default s3 bucket name --> fmtm-data
- rename var S3_BUCKET_NAME_BASEMAPS --> S3_BUCKET_NAME
- generate uuid for background tasks automatically
- rename project_id --> odk_project_id for clarity
- rename get odk project details for clarity
- remove unused project_crud function
- remove ref to project_export for now

## 0.1.0 (2023-11-08)

### Feat

- api to get data extracts for the given aoi and category (#960)
- added Pagination info in the project summary (#959)
- selection of basemap output formats, TMS input, mobile UI (#896)
- add Minio to backend compose stack & CI (#908)
- addressing of project using Nominatim (#913)
- new UI for create project (#918)
- backend tests for project endpoints (#900)
- add map clustering on main page (#905)
- returned required media name in a response of form validity (#871)
- remove microfrontend (#831)
- data extract custom
- map integration on project list map
- project centroid api integration on project summary
- package changes of ol and added to main
- added alchemy text on centroid api
- map Component added to main
- add script to generate openapi.json
-  Added a new function to perform the conversion of task_boundary from GeoJSON to .osm format.
- download button for data extract on project details fix Add option to download the data extract fix #779
- api for download data extract
- added download data extract loading
- Enhance GeoJSON Handling and Support for Multiple Formats during task spliting
- added custom road extract
- use loguru stdout + json file logging
- form validation added on custom form
- added organisation_id on create project frontend
- organisation Id  on create project api
- added api to centroid logo
- added projectId on projectbyid
- Tailwindcss integrated
- added mbtiles ui and functionality
- scale reduced on map icon
- order change define task and data extract
- typescript integration
- api to test the validity of custom form uploaded
- tile generation process moved into fastapi background task
- josm zoom and load added
- bounds in geometry_to_geojson
- josm zoom and load added
- bounds in geometry_to_geojson
- get all submissions
- submission json of a project
- Draw AOI
- added react on import
- draw in progress
- Login signup handled for local docker
- Log Status added on UI
- edit form with form category WIP
- HashTag Project Create
- login osm added
- removed serviceworker in development
- app on scheme of intent for redirect to odk collect app
- webpack changes for pwa
- added manifest.json for pwa
- integrated serviceworker for pwa
- workbox config on webpack
- added workbox for pwa
- data extracts on the update project form
- organization another page redirect
- popup changed to another file
- changed head title
- fmtm dev and prod domain to tracepropagationtargets
- sentry setup for production but dev dsn missing
- removed glitchtip test button ui
- integrated sentry alternative glitchtip
- update project boundary added constant
- added outline_geojson on project info
- added EditProject Area on Webpack exposes
- fix task_status to String
- refactored typescript files
- download form of project
- forgot password route removed
- eslint prettier setup
- new tsconfig setup
- added back icon on EditProject
- added ArrowBackIcon on assetmodules
- backbutton on projectinfo page
- edit project details
- added outline css to debug
- slice for edit project
- edit project validation
- edit project sidebarContent constant
- added patch for project details
- added nodeenv on environment
- Added Edit Project button
- current location trigger
- create organization button on create project
- osm auth login completed
- Improved Auto-Fill for ODK Central URL and Username Fields Resolve #566
- added slice for uploading area geojson
- added editproject component
- set individual project details to slices
- changed name of modal from create to default
- individual project detail api
- routes added for project edit
- data extract step added
- accept extension on input of upload area
- added validation for dataextract step
- data Extract step added on create project page
- added input file accept extension
- Data Extract Step added with functionality changes
- Added Route For Data Extract Step
- Modify AOI feature
- redirected to project specific detail page after project creation
- project creating loading
- generate task loader and disable handled
- organization logo required field removed
- projection switched to EPSG:3857
- implemented api logic for loading button of download
- csv and json loader added with style changes
- added mui/lab loadingbutton on coremodules
- added mui/lab package
- fixed project info download submission
- condition for empty file submission api
- form issue fixes on geojson upload
- added padding on map layers
- added task locking and disabled showing option to change task status
- osm auth fix
- package changes
- osm auth fix 1
- removed org type from backend
- implemented new tab on sidebar
- Tasks Page For Submission
- env generation script for easier first setup
- progress bar integrated
- fixed form issues
- submission json api
- download submission to an individual submission
- exception in creating a project in odk central
- added osm extracts into fmtm db
- submission points api
- generate app user files is moved in background task
- dynamic project id based submission
- download submission api
- avatar png added for submission by
- added submission page on webpack to expose
- form-list api, app users list api
- basic typescript config will add more config
- category removed from generate api . Category is taken from project table, of from form itself
- list submission for the project api created
- organization dropdown create project
- route added for basemap selection
- basemap selection page added
- removed user input field and added central odk input field
- added type on Validation of Create project
- custom pagination function
- prettier added
- endpoint to get the qr code by task created
- endpoint to list the xforms
- end point to upload multi polygon file to create a task for each polygon in the file
- missing validation on upload geojson
- put and patch api for project informations
- add endpoint load-test-data for local zip import
- add test_data_path for test data dir
- replace backend dotenv config with Pydantic BaseSettings
- add config file for fastapi/pydantic env settings
- removed listProjects during backend init, partial list central projects endpoint
- add root_path option to FastAPI for serving behind proxy subpath

### Fix

- ads qr code to task list (#970)
- create new project ux tweaks (#969)
- create new project ui/ux improvements (#955)
- align new organization button, replace total projects text (#947)
- signin / out buttons on mobile (#939)
- basemap modal closes menu (#938)
- replace iterative approach for task feats, edit schema
- move simplify features to get_project_features endpoint (#933)
- simplify project features response & prep for flatgeobuf osm extracts (#932)
- warning message before project creation action is cancelled (#924)
- removed icon from activities
- inform user if GeoJSON CRS is not EPSG:4326 (#919)
- allow specifying API_PREFIX if behind proxy
- optimise mobile UI - project info, home, organisation (#903)
- feature count in task features count api (#904)
- solved tasking splitting issue
- issue when single feature polygon uploaded to upload multi polygon api
- trim whitespace on schema check prior to migrate (#886)
- solved unsupported multi-linestring custom feature issue in odk … (#865)
- set underpass api url via env var
- remove data extract on different dropdown selection
- edit project symbol changes on regex
- commented pagination for future
- create project single AOI
- outline geojson of project in project details api (#825)
- project info on click
- callback url
- logs filters for project creation
- raw sql query in tasks feature
- remove pydantic Url in favour of str (#814)
- tiles generation
- map_url and main_url in config file
- cors origin error
- task split algorithm
- updated category based on the available yaml file
- pydantic defaults for ODK_CENTRAL vars (#806)
- import error in json2osm
- list forms api
- import error in json2osm
- upload media if the task has zero features, do not upload media
- validate EXTRA_CORS_URLS before model validation
- refactor pydantic v2 Config class (no orm_mode)
- set default vals for all settingss pydantic v2
- typing for pydantic validator Url
- pydantic v1 BaseSettings --> v2 pydantic_settings
- removed project detail from lazy loading white screen
- Add support for Doxygen API output
- Fix import path for read_xlsforms
- Read in all the xlsforms at startup time
- project name validation fix Project name should accept other characters too. #754
- submission detail page
- organization_id added on create project
- minimum 5 of splitting algorithm
- Project name should accept other characters too. #754
- organization_id none case handled
- task  splitted is not shown in map, although the number of tasks are determined and generated  #750
- previous button wrong route issue
- project_id added in the tile_instance
- set tile_path_instance outside try, ref before assign
- set tile download dir to volume path
- task status updated issue
- only set OAUTHLIB_INSECURE_TRANSPORT in DEBUG mode
- questions order in odk collect
- Generate mbtiles ux
- removed async from background mbtiles task
- project info page not showing projectarea
- removed drawn geojson on route change
- hashtag validation create project
- Color Changes of Tasks and Lock added
- user with existing username in osm login
- submission detail page undefined
- user with existing username in osm login
- submission detail page undefined
- if osm is None, return None
- coonvert to osm function updated if the submission is not present
- tasks features api
- Draw AOI bug fix
- create project value change on edit
- task aplit algrithm for gojson type feature
- features api
- remove SQLALCHEMY_DB_URL in favour of FMTM_DB_URL
- check for valid geometry in task generate
- central api create odk form
- task aplit algorithm, seek to the first object of in memory file
- upload geojson type Polygon
- update category api
- workbox webpack fix for loop
- submission logic to download json file of task changed
- task-features api with undefined issue
- seek for in memory file used in multipolygon upload
- upload boundary, seek(0) used for in memory file
- go to odk temp fix
- intent
- pwa fixes for icon
- merge conflicts
- data Cleaning fix
-  removed api listing static content
- projects can be filter based on user_id and hashtags present in the project
- filtering by hashtags check if project hashtags overlap with requested hashtags
- task spliting for geojson with polygons instead of features
- download task geometries
- download project outline
- merge xlsforms import from main --> development
- multi polygon
- merge conflict
- generate_appuser_files json loads the one.outline instead of eval
- generate files
- width on Update form adjusted
- removed prefix from project patch put api
- organization list not populating
- merge conflicts
- query to split algorithm
- osm extracts function
- osm auth login
- osm auth test 5
- osm auth test 2
- osm auth login test fix 1
- removed unused import
- removed organization actions
- removed unwanted code on define area map
- removed unwanted constant
- Global View of map - Create Project : Initially the global map should be displayed by default. resolve#461
- custom file upload not showing switching step
- using favicon.ico instead of favicon.png for better cross browser support including firefox
- project detail metadata not showing
- legend fix on mobile view
- task wise submission export download
- file extension passed in generate files
- download json and csv submission
- changed default dimension number to 10
- debug routes import error
- deleting projectd. Passed odk credentials
- task list
- upload multi polygon fix
- removed project details data after page changes
- form file is required handled
- add missing fmtm_images volume def to prod compose
- task_feature_count api submission count
- osm-fieldwork version issue
- osm login
- osm auth login fix
- osm auth fix
- osm auth fix
- osm auth login fix
- osm login test
- osm login test 2
- osm auth with json response added on /me/
- osm auth fix 4
- json response on osm callback url
- osm auth fix
- osm auth fix
- osm auth login fix
- osm authlogin test 1
- error on Project info page
- osm-fieldwork import
- osm-fieldwork imports
- Fixes Create Project Section : The input file name has design issues. #452
- Create Project Section - Upload Area subsection : Alignment of the map elements need to be maintained.  #451
- handle click outside issue
- organization post
- adjusted map page of home
- merge conflict
- link fix on hotosm.org
- remove lorem ipsum
- typo
- style chnaged
- ExlploreProjectCard style changed
- get_user in create project
- indentatio n fixes
- remove Multiple feature api
- init submission xforms with OdkForm(odk_central)
- load test data endpoint
- references to central_crud global project/task
- linting errors for backend
- pydantic settings default DEBUG type bool
- odkcentral api user init script variables
- bug on select form upload
- create project custom form issue
- centroid extracts outside project area
- imports
- category error for custom form in generate osm data
- xlsfile params in osm extracts
- data extract ways for create project
- osm extracts upload
- form issue on create project
- osm 6
- osm auth 5
- osm auth 3
- Osm test 2
- osmauth fix 1
- continue loop only in extractPolygon type
- upload custom xlsfrm in generate app files api
- Multipolygon type in divide into square
- logger error
- changed tsx to jsx on openlayer map module
- task list api
- optional chaining operator added on dialogtaskactions.jsx
- multipolygon issue in creating boundary
- project details form dropdown changed from rsuite to material ui
- removed project persist (causing issue)
- changed outdir file to dist and tsconfig replaced
- removed project id from upload xlsform
- removed xform_title from generate appuser
- osm_extracts in upload media
- qr code generate url
- added missed slash in the server url
- odk collect QR read
- generate working qr code
- adding odk server credentials to the projects table
- Change shapely from 1.8.5 to 2.0.1 to get the centroid function instad of the attribute
- removed console log
- all usages of odkconvert are now osm-fieldwork
- login response issue
- merge conflict
- port binding for pytest workflow.
- check for None type in cors origin validation
- make BACKEND_CORS_ORIGINS optional, rename to EXTRA_CORS_ORIGINS
- bug fix on project details
- prettier fixes
- linting
- project summary api
- merge conflict and instructions removed from load_test_data function
- get_users throwing an error when no users in db
- osm login
- revert self --> cls in pydantic base settings, ignore N805
- osm auth routes, json encode responses
- add init file to test data dir to make discoverable
- include task_status_str in status update response
- remove symlinked frontend prod dockerfiles, builds failing
- missed dockerfile for odkcentral in compose prod
- QR insert w/ project zip upload, QR base64 w/ get project tasks
- /central/appuser endpoint, return qr code
- add fmtm.hotosm.org to backend cors origins (until configurable)
- fmtm network for traefik in prod deploy
- revert pytest run from src dir, run from root
- add pytest to requirements-dev and lock all versions
- add API_URL to frontend env in docker-compose
- update imports to odkconvert using pip pkg
- manually create StrEnum,IntEnum in python 3.11 (allow >3.9)

### Refactor

- update changelog path for commitizen
- change version 0.1.0 --> 0.0.0 prior to first bump
- add package.json to version control files
- remove S3_BUCKET_NAME_OVERLAYS (handled by raw-data-api)
- update final refs to GenerateMbTiles --> GenerateBasemap
- remove package-lock.json (not used)
- remove make_data_extract replace with osm-rawdata (#891)
- remove console.log for import.meta.env
- update refs to frontend/main --> frontend
- use full links to hotosm logo in readme
- remove ogr2osm in code
- replace all instances of standard logging
- add additional defaults to backend settings
- remove api login/signup endpoints
- remove manual login/logout from frontend
- remove NODE_ENV check for login buttons
- use postMessage OSM login, avoid CORS devserver
- additional logs during proj creation
- revert ports on debug compose config
- add init file to backend images dir
- odk init script to trigger workflow
- move backend files back to /app after rebase
- move backend out of /app prior to rebase
- lint and format all markdown files
- run pre-commit hooks on backend
- move app backend server files to app dir
- move backend code out of app dir for rebase
- add additional logging to odkcentral connection
- update __version__.py path in pyproject.toml
- remove FMTM_TEST_DB_NAME, DB_URL --> FMTM_DB_URL
- ignore osm-fieldwork local dir
- remove tests dir in root (under src dirs)
- run pre-commit hooks on backend files
- move backend files to app dir
- change useless root api path to redirect to /docs
- move osm auth init to separate file, use Depends
- move debug data import logic to crud, routes call method
- remove read_xlsforms from project routes, moved to app start
- move test data into backend directory, bundle in dockerfile
- rename quay images in compose
- remove logs dir clutter
- remove learn_fastapi clutter
- remove odkcentral api and proxy into separate dir
- add log during central create_appuser return
- temp add additional frontend hosts to api cors origins
- remove unused frontend dockerfiles and compose
- remove redundant flask tests (demo frontend)
- remove custom traefik image, set via command & labels in compose
- add image names to docker-compose file (github container reg)
- add default for db .env vars, not required for dev setup
- remove src/web demo flask app
- remove demo flask app from prod docker-compose
- removed LOCAL_DB_URL env var
- cleanup .env example, remove config.py for flask demo
- remove submodules (wiki --> docs, odkconvert --> pip pkg)
- remove odkconvert from repo (install instead)
