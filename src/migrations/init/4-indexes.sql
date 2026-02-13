CREATE INDEX idx_projects_outline ON public.projects USING gist (outline);

CREATE INDEX idx_user_roles ON public.user_roles USING btree (
    project_id, user_sub
);

CREATE INDEX idx_api_keys_hash ON public.api_keys USING btree (key_hash);

CREATE INDEX idx_api_keys_user_sub ON public.api_keys USING btree (user_sub);
