ALTER TABLE ONLY public.projects
ADD CONSTRAINT fk_users FOREIGN KEY (created_by_sub)
REFERENCES public.users (
    sub
);
