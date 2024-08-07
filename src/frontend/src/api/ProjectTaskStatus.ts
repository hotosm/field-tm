import { ProjectActions } from '@/store/slices/ProjectSlice';
import { HomeActions } from '@/store/slices/HomeSlice';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { projectTaskBoundriesType } from '@/models/project/projectModel';

const UpdateTaskStatus = (
  url: string,
  style: any,
  existingData: projectTaskBoundriesType[],
  currentProjectId: string,
  feature: Record<string, any>,
  taskId: number,
  body: any,
  params: { project_id: string },
) => {
  return async (dispatch) => {
    const updateTask = async (url: string, body: any, feature: Record<string, any>, params: { project_id: string }) => {
      try {
        dispatch(CommonActions.SetLoading(true));

        const response = await CoreModules.axios.post(url, body, { params });
        dispatch(ProjectActions.UpdateProjectTaskActivity(response.data));

        await feature.setStyle(style);

        // assign userId to locked_by_user if status is locked_for_mapping or locked_for_validation
        const prevProperties = feature.getProperties();
        const isTaskLocked = ['LOCKED_FOR_MAPPING', 'LOCKED_FOR_VALIDATION'].includes(response.data.status);
        const updatedProperties = { ...prevProperties, locked_by_user: isTaskLocked ? body.id : null };
        feature.setProperties(updatedProperties);

        dispatch(
          ProjectActions.UpdateProjectTaskBoundries({
            projectId: currentProjectId,
            taskId,
            locked_by_uid: body?.id,
            locked_by_username: body?.username,
            task_status: response.data.status,
          }),
        );
        dispatch(CommonActions.SetLoading(false));
        dispatch(
          HomeActions.SetSnackBar({
            open: true,
            message: `Task #${taskId} has been updated to ${response.data.status}`,
            variant: 'success',
            duration: 3000,
          }),
        );
      } catch (error) {
        dispatch(CommonActions.SetLoading(false));
        dispatch(
          HomeActions.SetSnackBar({
            open: true,
            message: `Failed to update Task #${taskId}`,
            variant: 'error',
            duration: 4000,
          }),
        );
      }
    };
    await updateTask(url, body, feature, params);
  };
};

export default UpdateTaskStatus;
