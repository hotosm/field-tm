import axios from "axios";
import { ProjectActions } from "../store/slices/ProjectSlice";
import { easeIn, easeOut } from 'ol/easing';
import { HomeActions } from 'fmtm/HomeSlice';
import Style from "ol/style/Style";
import Icon from "ol/style/Icon";
const UpdateTaskStatus = (url, style, existingData, currentProjectId, feature, map, view, taskId, body) => {

    return async (dispatch) => {

        const index = existingData.findIndex(project => project.id == currentProjectId);
        const updateTask = async (url, existingData, body) => {

            try {
                dispatch(HomeActions.SetDialogStatus(false))
                map.getTargetElement().classList.add('spinner');

                const response = await axios.post(url, body);
                const findIndexForUpdation = existingData[index].taskBoundries.findIndex(obj => obj.id == response.data.id)

                let project_tasks = [...existingData[index].taskBoundries]
                project_tasks[findIndexForUpdation] = { ...response.data }

                let updatedProject = [...existingData]
                const finalProjectOBJ = { id: updatedProject[index].id, taskBoundries: project_tasks }
                updatedProject[index] = finalProjectOBJ;

                dispatch(ProjectActions.SetProjectTaskBoundries(updatedProject))

                dispatch(HomeActions.SetSnackBar({
                    open: true,
                    message: `Task #${response.data.id} updated successful`,
                    variant: 'success',
                    duration: 6000
                }))


            } catch (error) {
                dispatch(HomeActions.SetSnackBar({
                    open: true,
                    message: `Failed to update Task #${taskId}`,
                    variant: 'error',
                    duration: 6000
                }))
            }

        }
        await updateTask(url, existingData, body)
        const centroid = await existingData[index].
            taskBoundries.filter((task) => {
                return task.id == taskId
            })[0].outline_centroid.geometry.coordinates;

        await feature.setStyle(style)
        await map.getView().setCenter(centroid)
        setTimeout(() => {
            view.animate({ zoom: 20, easing: easeOut, duration: 2000, });
        }, 100);
    }
}

export default UpdateTaskStatus;