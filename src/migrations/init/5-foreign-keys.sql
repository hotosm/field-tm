ALTER TABLE ONLY projects
ADD CONSTRAINT fk_users FOREIGN KEY (created_by_sub)
REFERENCES users (
    sub
);

ALTER TABLE ONLY user_roles
ADD CONSTRAINT user_roles_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES projects (id);

ALTER TABLE ONLY user_roles
ADD CONSTRAINT user_roles_user_sub_fkey FOREIGN KEY (
    user_sub
) REFERENCES users (sub);

ALTER TABLE ONLY api_keys
ADD CONSTRAINT api_keys_user_sub_fkey FOREIGN KEY (
    user_sub
) REFERENCES users (sub) ON DELETE CASCADE;
