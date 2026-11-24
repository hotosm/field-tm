#!/bin/sh
# Repack @electric-sql/pglite-postgis's 19 MB bundle with only what the splitter
# needs (~7 MB): core PostGIS, its install SQL and proj.db (geography casts fail
# without it). Raster, topology, tiger and upgrade scripts are dropped.
# Used by src/lib/engine/db.ts. Add files here if new PostGIS features are used.
set -eu
cd "$(dirname "$0")/.."

src=node_modules/@electric-sql/pglite-postgis/dist/postgis.tar.gz
out=src/lib/engine/postgis-slim.tar.gz
[ "$out" -nt "$src" ] && exit 0

ext=share/postgresql/extension
version=$(tar -xzOf "$src" "$ext/postgis.control" | sed -n "s/^default_version = '\(.*\)'/\1/p")
files="lib/postgresql/postgis-3.so $ext/postgis.control $ext/postgis--$version.sql share/proj/proj.db share/proj/proj.ini"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
tar -xzf "$src" -C "$tmp" $files
tar -czf "$out" -C "$tmp" $files
