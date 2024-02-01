# QR Code Utils

## Convert QR Code to JSON

```bash
cat /path/to/your/qrcode.png | \
    docker run -i --rm ghcr.io/hotosm/fmtm/qrcodes:latest --read
```

This will output the JSON data to terminal.

## Convert JSON to QR Code

```bash
cat file.json | \
docker run -i --rm ghcr.io/hotosm/fmtm/qrcodes:latest --write > qr.png
```

Alternatively pipe from STDIN on the command line:

```bash
echo '{
  "general": {
    "server_url": "https://url/v1/key/token/projects/projectid",
    "form_update_mode": "manual",
    "basemap_source": "osm",
    "autosend": "wifi_and_cellular",
    "metadata_username": "svcfmtm",
    "metadata_email": "test"
  },
  "project": {
    "name": "task qrcode conversion"
  },
  "admin": {}
}' | docker run -i --rm ghcr.io/hotosm/fmtm/qrcodes:latest --write \
> qr.png
```

This will create a file `qr.png` from your data.
