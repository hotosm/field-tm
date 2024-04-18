import { ProjectActions } from '@/store/slices/ProjectSlice';
import { HomeActions } from '@/store/slices/HomeSlice';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { task_priority_str } from '@/types/enums';

const UpdateTaskStatus = (url, style, existingData, currentProjectId, feature, map, view, taskId, body, params) => {
  return async (dispatch) => {
    const updateTask = async (url, existingData, body, feature, params) => {
      try {
        dispatch(CommonActions.SetLoading(true));

        const response = await CoreModules.axios.post(url, body, { params });
        dispatch(ProjectActions.UpdateProjectTaskActivity(response.data));

        await feature.setStyle(style);
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
