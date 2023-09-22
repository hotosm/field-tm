import CoreModules from '../shared/CoreModules';
import { ProjectActions } from '../store/slices/ProjectSlice';
// import { HomeProjectCardModel } from '../models/home/homeModel';

export const ProjectSubmissionService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(ProjectActions.GetProjectSubmissionLoading(true));

    const fetchProjectSubmission = async (url: string) => {
      try {
        const fetchSubmissionData = await CoreModules.axios.get(url);
        const resp: any = fetchSubmissionData.data;
        dispatch(ProjectActions.SetProjectSubmission(resp));
        dispatch(ProjectActions.GetProjectSubmissionLoading(false));
      } catch (error) {
        dispatch(ProjectActions.GetProjectSubmissionLoading(false));
      }
    };

    await fetchProjectSubmission(url);
  };
};
export const ProjectBuildingGeojsonService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(ProjectActions.GetProjectBuildingGeojsonLoading(true));

    const fetchProjectBuildingGeojson = async (url: string) => {
      try {
        const fetchBuildingGeojsonData = await CoreModules.axios.get(url);
        const resp: any = fetchBuildingGeojsonData.data;
        dispatch(ProjectActions.SetProjectBuildingGeojson(resp));
        dispatch(ProjectActions.GetProjectBuildingGeojsonLoading(false));
      } catch (error) {
        dispatch(ProjectActions.GetProjectBuildingGeojsonLoading(false));
      }
    };

    await fetchProjectBuildingGeojson(url);
  };
};
