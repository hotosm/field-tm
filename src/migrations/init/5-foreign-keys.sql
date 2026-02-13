ALTER TABLE ONLY public.projects
ADD CONSTRAINT fk_users FOREIGN KEY (created_by_sub)
REFERENCES public.users (
    sub
);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_user_sub_fkey FOREIGN KEY (
    user_sub
) REFERENCES public.users (sub);

ALTER TABLE ONLY public.api_keys
ADD CONSTRAINT api_keys_user_sub_fkey FOREIGN KEY (
    user_sub
) REFERENCES public.users (sub) ON DELETE CASCADE;
