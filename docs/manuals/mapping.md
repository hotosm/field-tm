# Field Mappers

The **Mapper Page** was developed to provide a simpler, more intuitive
mapping experience for field mappers.

## Prerequisites

### Device Requirements

Verify that your mobile device meets the minimum specifications required
for field mapping:

- **RAM**: 3GB
- **Storage**: Generally 1GB should be enough, but if using many large basemaps,
  more may be required.
- **Operating System**: Android 10 or higher for the best security and
  performance.

  !!! tip

        Go to the file manager or "My Files" on your mobile device to see
        the device storage.

        Check your phone settings for information about device settings
        such as RAM and processors.

### Install FieldTM

- We recommend using Chrome-based browsers on your mobile device to access
  the Field-TM platform for optimal performance.
- It is best to **install** the web application (not via the app store, but through
  your web browser). This can be done through the browser menu, often written as
  'Add to home screen':
  ![image](https://github.com/user-attachments/assets/03bd53fb-3879-4a11-a98e-6c8e2651210a)

## Part (A): Setup For Mapping

### Step 1: Access the Mapper Page

- **Option 1:** Click on the project cards from your mobile device
- **Option 2:** Go to `https://mapper.fmtm.hotosm.org/<project_id>` to open
  the Mapper Page for a specific project.

!!! note

      This functionality is designed for mappers in the field, so it is
      recommended to use a mobile device to access it. If you use a computer
      browser, you will be redirected to the project details page instead of
      mapper's page.

!!! warning

      Here you may log into the website to be attributed with you edits.

      If you do not log in, a generic account will be used to record your
      edits and data collection.

### Step 2: Load Imagery (optional)

- You can load the base imagery by clicking on offline mode option
  (second tab on bottom navigation bar).
- Choose the layer you want to load and click on **Show on Map** to visualise
  the layer on map.
- The layer can also be stored for offline mapping by clicking
  **Store Offline**.

  ![offline-pmtiles](https://github.com/user-attachments/assets/1c091df2-2db0-4546-b600-e2a3a339b981)

!!! tip

      This step should probably be done prior to leaving for the field!

      The files can be a few 100MB in size.

      MBTiles are used for loading into ODK Collect.
      PMTiles are used for navigating in Field-TM.

      If you encounter issues with the base imagery, contact your project
      manager.

### Step 3: Install The Custom ODK Collect Mobile App

!!! note

    It is recommended to not use ODK Collect in most, but instead use the
    automatically configured WebForms.

    If you must use ODK Collect, then configuration via QRCodes will be required.

- The first time you load the project, you should be prompted to download
  the custom ODK `.apk` from the sidebar.
- Once downloaded, you should install the custom ODK Collect application.

  ![highlighted-sidebar](https://github.com/user-attachments/assets/53de2d80-2709-45b0-bb82-32f0190c7859)
  ![download-custom-odk](https://github.com/user-attachments/assets/22501751-4962-4cd7-ace1-7587269ae16c)

!!! tip

      If you already have ODK Collect installed, you may have to uninstall
      it first.

      You may have to enable installing from unknown sources in your device
      settings too.

### Step 4: Configure ODK Collect (once only)

- **Option 1:** Scan the QR code displayed on the Mapper page using
  the custom ODK Collect mobile application.

- **Option 2:** Download the QR code and import it into ODK Collect to
  load the project. Follow the steps below:
  1. Open ODK Collect.
  2. Click the project name in the top right corner.
  3. Tap the **menu** icon (three horizontal dots).
  4. Select **Import QR Code**.
  5. Browse to the downloaded QR image and load the project.

!!! tip

      For a demonstration of the process above, click the **i** info icon
      on the QR Code tab of the mapper page.

## Part (B): Mapping Features

Before starting to map features, ensure that geolocation is enabled.
This will allow you to access your live location, making navigation easier.

You may either map an **existing feature** OR map a **new feature**.

### Select An Existing Feature via ODK Collect

In most cases we are submitting a survey about a feature that already exists.

- Click on a task area: the features within will be displayed.
- Now click on a feature you wish to map: a popup will appear.
- Now click 'Map Feature In ODK': ODK Collect will open, with the
  feature pre-selected in the survey (no need to open the ODK map!).
- If the feature you are trying to map is further than 50m away, you will
  be prompted with warning message to ensure you made the correct selection.
- Complete the survey and submit.

![IMG_20250109_160742](https://github.com/user-attachments/assets/bf350d1c-c80e-42ee-970b-ca71a3713a9f)

!!! tip

      You may manually click 'Start Mapping' for a task area.

      However, the task will be automatically locked for you
      if you map a feature within the task area.

!!! note

      The task area will change colour based on it's status.

      The legend explaining these colours can be opened on the map:

      ![legend](https://github.com/user-attachments/assets/280fd927-b71e-4336-a89a-1672e8de687b)

### Select An Existing Feature via WebForms

Webform is the new functionality added on FMTM, where mappers can directly
fill up and upload form via same browser without installing ODK Collect
mobile application.

- Click on a task area: the features within will be displayed.
- Now click on a feature you wish to map: a popup will appear.
- Click on 'Collect Data' which will open the form directly on the same browser.
- Complete the survey and Upload.

  ![image](https://github.com/user-attachments/assets/b4a6901b-5c9e-4c45-b25d-ceb4dc299eae)

!!!note

    Currently, we need to have stable internet connection to upload the survey.
    We expect offline saving of form on local and sync when
    internet is available functionality on next release.

### Mapping A New Feature

Sometimes the feature does not exist on the map yet!

- Click on a task area: a popup will display.
- At the top right, there is a button **Map New Feature**.
- Click on the map to create a new geometry.
- Once drawn, accept the dialog to confirm the geometry is correct.
- If you are using ODK Collect, you will be redirected to ODK Collect to fill
  out the survey data for the newly created feature.
  -If you are using WebForms used for that project, form will be opened on
  the same browser and you can fill out the survey for that feature.
  ![IMG_20250109_160816](https://github.com/user-attachments/assets/98b70f5a-4db8-46cb-84ae-58bec07c82c1)

!!! note

      The task area will change colour based on it's status.

      Consult the project manager to determine if the feature should be a
      polygon (drawing all corners of the feature in ODK) or point
      (collecting only the GPS point of the feature).

      Confirm the exact point (gate location, right corner, center of the
      building) and GPS accuracy required for consistency and quality data.

### Repeat The Process

- After ODK collect based form submission, you have to get back to
  Field-TM and select the another feature for mapping.
- After WebForm based form submission, you will automatically get back to mapper's
  page where you can select another feature for mapping.
- You also also have to click the **Sync Status** button to see the feature
  turn green.

  ![sync-status-button](https://github.com/user-attachments/assets/38062aad-c8ea-4d47-a617-4be70dbfa20c)

- Select another feature to map (repeat from step 5)!

!!! note

      You need internet access to update the feature status.

      In a future release, this process will be handled seamlessly
      without user interaction.

## Working Offline

It is possible to work entirely offline, once FieldTM has been loaded
while internet is available.

To achieve this:

- Visit [https://mapper.fmtm.hotosm.org](https://mapper.fmtm.hotosm.org)
  once from the phone you wish to map with.
  - This will cache the 12 most recent projects on your device.
  - To cache a different set of projects, use the search or
    next/previous page functionality.
- For best results, 'Install' the webpage on your device, creating
  a shortcut on your home screen.
- Click on the project you wish to map offline.
  - The project details will be stored entirely offline.
  - You may also go to the 'Offline' tab, to download additional
    offline data such as base map imagery.
- Upon opening the installed app, you should be able to browse
  the cached versions of your projects (note they will not update
  while offline).
- Submissions can be made while offline & they will since when
  connectivity is restored.

## Upcoming improvements

Refer the milestone: <https://github.com/hotosm/fmtm/milestone/49>
