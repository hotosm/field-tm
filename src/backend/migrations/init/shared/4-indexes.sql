CREATE INDEX idx_task_event_composite
ON public.task_events USING btree (
    task_id, project_id
);
CREATE INDEX idx_task_event_project_user
ON public.task_events USING btree (
    user_sub, project_id
);
CREATE INDEX idx_task_event_project_id
ON public.task_events USING btree (
    task_id, project_id
);
CREATE INDEX idx_task_event_user_sub
ON public.task_events USING btree (
    task_id, user_sub
);
CREATE INDEX idx_entities_project_id
ON public.odk_entities USING btree (
    entity_id, project_id
);
CREATE INDEX idx_entities_task_id
ON public.odk_entities USING btree (
    entity_id, task_id
);
CREATE INDEX idx_geometrylog_geojson
ON public.geometrylog USING gin (geojson);
