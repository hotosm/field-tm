CREATE INDEX idx_projects_outline ON projects USING gist (outline);

CREATE INDEX idx_user_roles ON user_roles USING btree (
    project_id, user_sub
);
