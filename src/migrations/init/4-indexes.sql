-- Base schema files run against an empty database, so online migration
-- lock-safety checks do not apply here.
-- noqa: disable=PG01
CREATE INDEX idx_projects_outline ON projects USING gist (outline);

CREATE INDEX idx_user_roles ON user_roles USING btree (
    project_id, user_sub
);
-- noqa: enable=PG01
