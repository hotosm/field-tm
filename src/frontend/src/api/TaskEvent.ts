import { AppDispatch } from '@/store/Store';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { task_event as taskEventEnum, task_state as taskStateEnum } from '@/types/enums';

export const CreateTaskEvent = (
  url: string,
  action: taskEventEnum,
  currentProjectId: string,
  taskId: string,
  body: any,
  params: { project_id: string },
  style?: any,
  feature?: Record<string, any>,
) => {
  return async (dispatch: AppDispatch) => {
    const updateTask = async (
      url: string,
      body: any,
      params: { project_id: string },
      feature?: Record<string, any>,
    ) => {
      try {
        body = {
          event: action,
          ...body,
        };
        const response = await CoreModules.axios.post(url, body, { params });
        dispatch(ProjectActions.UpdateProjectTaskActivity(response.data));
        if (feature && style) {
          // update task color based on current state
          await feature.setStyle(style[response?.data?.state]);

          // assign userId to actioned_by_uid if state is locked_for_mapping or locked_for_validation
          const prevProperties = feature.getProperties();
          const isTaskLocked = [taskStateEnum.LOCKED_FOR_MAPPING, taskStateEnum.LOCKED_FOR_VALIDATION].includes(
            response.data.state,
          );
          const updatedProperties = { ...prevProperties, actioned_by_uid: isTaskLocked ? body.id : null };
          feature.setProperties(updatedProperties);

          dispatch(
            ProjectActions.UpdateProjectTaskBoundries({
              projectId: currentProjectId,
              taskId,
              actioned_by_uid: body?.id,
              actioned_by_username: body?.username,
              task_state: response.data.state,
            }),
          );
        }

        dispatch(
          CommonActions.SetSnackBar({
            message: `Task #${taskId} has been updated to ${response.data.state}`,
            variant: 'success',
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: `Failed to update Task #${taskId}`,
          }),
        );
      }
    };
    await updateTask(url, body, params, feature);
  };
};
