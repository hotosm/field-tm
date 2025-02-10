# Basemap Generator Image

This container image contains binaries for:

- <https://github.com/tilezen/go-tilepacks>
- <https://github.com/protomaps/go-pmtiles>

With these, we can generate an mbtiles file from TMS, then also convert to PMTiles.

## Usage

```bash
docker run --rm ghcr.io/hotosm/fmtm/basemap-generator:0.3.0 --help
```
