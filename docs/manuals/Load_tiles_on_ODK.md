# Loading MBTiles on ODK Collect

This guide provides detailed steps on how to manually load
MBTiles or custom tiles into the ODK Collect app for Android users.
The current process involves downloading the tiles from FMTM and
moving the MBTiles file to a specified path on your device.

## Steps for Android Users

### 1. Download and Copy the MBTiles File

- First, download the MBTiles file from the FMTM (Field Mapping Tile Manager).
- Once downloaded, locate the file on your device and copy it.
  The file will typically be in your "Downloads" folder unless you
  specified a different download location.

### 2. Navigate to the Destination Folder

- Open the "My Files" or "File Manager" app on your Android device.
- Navigate to the internal storage of your device by selecting `Device storage`.
- Follow the path: `Android -> data`.
- Locate the folder `org.odk.collect.android -> files -> layers`.
- If your device restricts access to this path, proceed to the
  alternative method below.

### 3. Alternative Method for Devices with Restricted Access

- Connect your mobile device to your computer using a data cable.
- Ensure you have enabled file transfer mode on your device.
  This setting can usually be found in the notification panel
  after connecting the cable.
- On your computer, open the file explorer and navigate to
  your device's storage.
- Follow the path: `Device storage -> Android -> data ->
org.odk.collect.android -> files -> layers`.
- Paste the copied MBTiles file into the `layers` folder.
  This action ensures that the MBTiles file is accessible to the ODK Collect app.

### 4. Enable MBTiles in ODK Collect

- Open the ODK Collect app on your Android device.
- Navigate to the project settings where you want to add the
- MBTiles.
  - You can access the settings by clicking on the three-dot
    menu or the gear icon, depending on your version of ODK Collect.
- Within the project settings, go to `Maps`.
- Click on `Layer` and you should see the MBTiles file you
  added. Enable this layer by selecting it.
- Save the changes to apply the new layer settings.

### 5. Load Custom Tiles in a New Form

- Now that the MBTiles are enabled, you can start a new form within ODK Collect.
- The custom tiles should automatically load on the map within the
  form, providing the customized mapping data you need.
