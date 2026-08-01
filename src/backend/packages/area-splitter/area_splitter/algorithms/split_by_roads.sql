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
