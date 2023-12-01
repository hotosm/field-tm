import { ProjectActions } from '../store/slices/ProjectSlice';
import { easeIn, easeOut } from 'ol/easing';
import { HomeActions } from '../store/slices/HomeSlice';
import CoreModules from '../shared/CoreModules';
import { CommonActions } from '../store/slices/CommonSlice';
const UpdateTaskStatus = (url, style, existingData, currentProjectId, feature, map, view, taskId, body) => {
  return async (dispatch) => {
    const index = existingData.findIndex((project) => project.id == currentProjectId);
    const updateTask = async (url, existingData, body, feature) => {
      try {
        dispatch(CommonActions.SetLoading(true));

        const response = await CoreModules.axios.post(url, body);
        const findIndexForUpdation = existingData[index].taskBoundries.findIndex((obj) => obj.id == response.data.id);

        let project_tasks = [...existingData[index].taskBoundries];
        project_tasks[findIndexForUpdation] = { ...response.data };

        let updatedProject = [...existingData];
        const finalProjectOBJ = {
          id: updatedProject[index].id,
          taskBoundries: project_tasks,
        };
        updatedProject[index] = finalProjectOBJ;

        dispatch(ProjectActions.SetProjectTaskBoundries(updatedProject));

        await feature.setStyle(style);
        dispatch(CommonActions.SetLoading(false));
        dispatch(
          HomeActions.SetSnackBar({
            open: true,
            message: `Task #${response.data.id} has been updated to ${response.data.task_status}`,
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
    await updateTask(url, existingData, body, feature);
    const centroid = await existingData[index].taskBoundries.filter((task) => {
      return task.id == taskId;
    })[0].outline_centroid.geometry.coordinates;
  };
};

export default UpdateTaskStatus;
