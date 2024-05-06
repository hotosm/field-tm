import { ProjectActions } from '@/store/slices/ProjectSlice';
import { HomeActions } from '@/store/slices/HomeSlice';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { task_status } from '@/types/enums';

const UpdateTaskStatus = (url, style, existingData, currentProjectId, feature, map, view, taskId, body, params) => {
  return async (dispatch) => {
    const updateTask = async (url, existingData, body, feature, params) => {
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
    await updateTask(url, existingData, body, feature, params);
  };
};

export default UpdateTaskStatus;
