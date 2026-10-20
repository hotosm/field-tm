-- Merge slivers (junction islands, dual carriageways, roundabouts) into the
-- neighbour with the longest shared edge: under 1000 m2, or under ~15 m wide
-- (2 * area / perimeter approximates the width of a thin strip).
DO $$
DECLARE
    sliver RECORD;
    nb RECORD;
BEGIN
    FOR sliver IN
        SELECT polyid FROM polygonsnocount ORDER BY ST_AREA(geog)
    LOOP
        SELECT p.polyid, p.geom INTO nb
        FROM polygonsnocount AS s, polygonsnocount AS p
        WHERE
            s.polyid = sliver.polyid
            AND (
                ST_AREA(s.geog) < 1000
                OR 2 * ST_AREA(s.geog) / NULLIF(ST_PERIMETER(s.geog), 0) < 15
            )
            AND p.polyid != s.polyid
            AND ST_TOUCHES(s.geom, p.geom)
            AND ST_DIMENSION(ST_INTERSECTION(s.geom, p.geom)) = 1
        ORDER BY ST_LENGTH(ST_INTERSECTION(s.geom, p.geom)) DESC
        LIMIT 1;
        IF FOUND THEN
            UPDATE polygonsnocount AS p
            SET geom = merged.geom, geog = merged.geom::geography
            FROM (
                SELECT ST_UNION(geom) AS geom FROM polygonsnocount
                WHERE polyid IN (sliver.polyid, nb.polyid)
            ) AS merged
            WHERE p.polyid = nb.polyid;
            DELETE FROM polygonsnocount WHERE polyid = sliver.polyid;
        END IF;
    END LOOP;
END $$;

-- Generate GeoJSON output directly from the road-bounded polygons
-- produced by common/1-linear-features.sql (polygonsnocount), with no
-- building-clustering/alignment steps in between.
SELECT
    JSONB_BUILD_OBJECT(
        'type', 'FeatureCollection',
        'features', JSONB_AGG(feature)
    )
FROM (
    SELECT
        JSONB_BUILD_OBJECT(
            'type', 'Feature',
            'geometry', ST_ASGEOJSON(t.geom)::jsonb,
            'properties', JSONB_BUILD_OBJECT(
                'building_count', (
                    SELECT COUNT(b.id)
                    FROM ways_poly AS b
                    WHERE
                        b.tags ->> 'building' IS NOT NULL
                        AND ST_CONTAINS(t.geom, ST_CENTROID(b.geom))
                )
            )
        ) AS feature
    FROM polygonsnocount AS t
) AS features;
