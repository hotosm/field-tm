import axios, { AxiosResponse } from 'axios';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { CommonActions } from '@/store/slices/CommonSlice';
import CoreModules from '@/shared/CoreModules';
import { task_state, task_event } from '@/types/enums';
import { EntityOsmMap, projectInfoType, projectTaskBoundriesType } from '@/models/project/projectModel';
import { TaskActions } from '@/store/slices/TaskSlice';
import { AppDispatch } from '@/store/Store';
import { featureType } from '@/store/types/IProject';

const VITE_API_URL = import.meta.env.VITE_API_URL;

export const ProjectById = (projectId: string) => {
  return async (dispatch: AppDispatch) => {
    const fetchProjectById = async (projectId: string) => {
      try {
        dispatch(ProjectActions.SetProjectDetialsLoading(true));
        const project = await CoreModules.axios.get(`${VITE_API_URL}/projects/${projectId}?project_id=${projectId}`);
        const projectResp: projectInfoType = project.data;
        const projectTaskIdIndexMap = {};
        const persistingValues = projectResp.tasks.map((data) => {
          projectTaskIdIndexMap[data.id] = data.project_task_index;
          return {
            id: data.id,
            index: data.project_task_index,
            outline: data.outline,
            task_state: task_state[data.task_state],
            actioned_by_uid: data.actioned_by_uid,
            actioned_by_username: data.actioned_by_username,
          };
        });
        // At top level id project id to object
        const projectTaskBoundries: projectTaskBoundriesType[] = [
          { id: projectResp.id, taskBoundries: persistingValues },
        ];
        dispatch(ProjectActions.SetProjectTaskBoundries([{ ...projectTaskBoundries[0] }]));
        dispatch(
          ProjectActions.SetProjectInfo({
            id: projectResp.id,
            outline: projectResp.outline,
            priority: projectResp.priority || 2,
            name: projectResp.name,
            location_str: projectResp.location_str,
            description: projectResp.description,
            num_contributors: projectResp.num_contributors,
            total_tasks: projectResp.total_tasks,
            osm_category: projectResp.osm_category,
            odk_form_id: projectResp?.odk_form_id,
            data_extract_url: projectResp.data_extract_url,
            instructions: projectResp?.per_task_instructions,
            odk_token: projectResp?.odk_token,
            custom_tms_url: projectResp?.custom_tms_url,
            created_at: projectResp?.created_at,
            visibility: projectResp.visibility,
            use_odk_collect: projectResp.use_odk_collect,
            primary_geom_type: projectResp.primary_geom_type,
            new_geom_type: projectResp.new_geom_type,
            status: projectResp.status,
            field_mapping_app: projectResp.field_mapping_app,
            external_project_id: projectResp.external_project_id,
            project_url: projectResp.project_url,
          }),
        );
        dispatch(ProjectActions.SetProjectTaskIdIndexMap(projectTaskIdIndexMap));
        dispatch(ProjectActions.SetProjectDetialsLoading(false));
      } catch (error) {
        if (error.response.status === 404) {
          dispatch(CommonActions.SetProjectNotFound(true));
        }
        dispatch(ProjectActions.SetProjectDetialsLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data.detail || 'Failed to fetch project.',
          }),
        );
      }
    };

    await fetchProjectById(projectId);
    dispatch(ProjectActions.SetNewProjectTrigger());
  };
};

export const DownloadBasemapFile = (url: string | null) => {
  return async (dispatch: AppDispatch) => {
    const downloadBasemapFromAPI = async (url: string) => {
      try {
        // Open S3 url directly
        window.open(url);
      } catch (error) {}
    };
    if (!url) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'No url associated to download basemap.',
        }),
      );
    } else {
      await downloadBasemapFromAPI(url);
    }
  };
};

export const GetEntityStatusList = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const getEntityOsmMap = async (url: string) => {
      try {
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(true));
        dispatch(TaskActions.SetTaskSubmissionStatesLoading(true));
        const response: AxiosResponse<EntityOsmMap[]> = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetEntityToOsmIdMapping(response.data));
        dispatch(TaskActions.SetTaskSubmissionStates(response.data));
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(false));
      } finally {
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(false));
        dispatch(TaskActions.SetTaskSubmissionStatesLoading(false));
      }
    };
    await getEntityOsmMap(url);
  };
};

export const GetProjectComments = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const getProjectComments = async (url: string) => {
      try {
        dispatch(ProjectActions.SetProjectGetCommentsLoading(true));
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetProjectCommentsList(response.data));
        dispatch(ProjectActions.SetProjectGetCommentsLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetProjectGetCommentsLoading(false));
      } finally {
        dispatch(ProjectActions.SetProjectGetCommentsLoading(false));
      }
    };
    await getProjectComments(url);
  };
};

export const PostProjectComments = (
  url: string,
  payload: { event?: task_event.COMMENT; task_id: number; comment: string },
) => {
  return async (dispatch: AppDispatch) => {
    const postProjectComments = async (url: string) => {
      try {
        dispatch(ProjectActions.SetPostProjectCommentsLoading(true));
        if (!('event' in payload)) {
          payload = { event: task_event.COMMENT, ...payload };
        }
        const response = await CoreModules.axios.post(url, payload);
        dispatch(ProjectActions.UpdateProjectCommentsList(response.data));
        dispatch(ProjectActions.SetPostProjectCommentsLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetPostProjectCommentsLoading(false));
      } finally {
        dispatch(ProjectActions.SetPostProjectCommentsLoading(false));
      }
    };
    await postProjectComments(url);
  };
};

export const GetProjectTaskActivity = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const getProjectActivity = async (url: string) => {
      try {
        dispatch(ProjectActions.SetProjectTaskActivityLoading(true));
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetProjectTaskActivity(response.data));
        dispatch(ProjectActions.SetProjectTaskActivityLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetProjectTaskActivityLoading(false));
      } finally {
        dispatch(ProjectActions.SetProjectTaskActivityLoading(false));
      }
    };
    await getProjectActivity(url);
  };
};

export const DeleteEntity = (url: string, project_id: number, entity_id: string) => {
  return async (dispatch: AppDispatch) => {
    const deleteEntity = async () => {
      try {
        dispatch(ProjectActions.SetIsEntityDeleting({ [entity_id]: true }));
        await axios.delete(url, { params: { project_id } });
        dispatch(ProjectActions.RemoveNewEntity(entity_id));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error?.response?.data?.detail || 'Failed to delete entity',
          }),
        );
      } finally {
        dispatch(ProjectActions.SetIsEntityDeleting({ [entity_id]: false }));
      }
    };
    await deleteEntity();
  };
};

export const SyncTaskState = (
  url: string,
  params: { project_id: string },
  taskBoundaryFeatures: any,
  geojsonStyles: any,
) => {
  return async (dispatch: AppDispatch) => {
    const syncTaskState = async () => {
      try {
        dispatch(ProjectActions.SyncTaskStateLoading(true));
        const response: AxiosResponse = await axios.get(url, { params });

        response.data.map((task) => {
          const feature = taskBoundaryFeatures?.find((feature) => feature.getId() === task.id);
          const previousProperties = feature.getProperties();
          feature.setProperties({
            ...previousProperties,
            task_state: task.task_state,
            actioned_by_uid: task.actioned_by_uid,
            actioned_by_username: task.actioned_by_username,
          });

          feature.setStyle(geojsonStyles[task.task_state]);

          dispatch(
            ProjectActions.UpdateProjectTaskBoundries({
              projectId: params.project_id,
              taskId: task.id,
              actioned_by_uid: task.actioned_by_uid,
              actioned_by_username: task.actioned_by_username,
              task_state: task.task_state,
            }),
          );
        });
      } catch (error) {
      } finally {
        dispatch(ProjectActions.SyncTaskStateLoading(false));
      }
    };
    await syncTaskState();
  };
};

export const GetOdkEntitiesGeojson = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const getProjectActivity = async (url: string) => {
      try {
        dispatch(ProjectActions.SetOdkEntitiesGeojsonLoading(true));
        const response: AxiosResponse<{ type: 'FeatureCollection'; features: featureType[] }> = await axios.get(url);
        dispatch(ProjectActions.SetOdkEntitiesGeojson(response.data));
      } catch (error) {
        dispatch(ProjectActions.SetOdkEntitiesGeojson({ type: 'FeatureCollection', features: [] }));
      } finally {
        dispatch(ProjectActions.SetOdkEntitiesGeojsonLoading(false));
      }
    };
    await getProjectActivity(url);
  };
};

export const UnassignUserFromProject = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const unassignUserFromProject = async (url: string) => {
      try {
        dispatch(ProjectActions.UnassigningUserFromProject(true));
        await axios.delete(url);
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error?.response?.data?.detail || 'Failed to unassign user from project',
          }),
        );
      } finally {
        dispatch(ProjectActions.UnassigningUserFromProject(false));
      }
    };
    await unassignUserFromProject(url);
  };
};
