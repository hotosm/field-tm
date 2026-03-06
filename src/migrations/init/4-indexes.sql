CREATE INDEX idx_projects_outline ON projects USING gist (outline);

CREATE INDEX idx_user_roles ON user_roles USING btree (
    project_id, user_sub
);

CREATE INDEX idx_api_keys_hash ON api_keys USING btree (key_hash);

CREATE INDEX idx_api_keys_user_sub ON api_keys USING btree (user_sub);
