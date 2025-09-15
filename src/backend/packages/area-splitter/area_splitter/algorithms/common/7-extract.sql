-- Generate GeoJSON output
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
                    FROM buildings AS b
                    WHERE ST_CONTAINS(t.geom, b.geom)
                )
            )
        ) AS feature
    FROM taskpolygons AS t
) AS features;
