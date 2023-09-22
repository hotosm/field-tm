import axios from 'axios';
import { HomeActions } from '../store/slices/HomeSlice';
import { HomeProjectCardModel } from '../models/home/homeModel';
import environment from '../environment';

export const HomeSummaryService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(HomeActions.HomeProjectLoading(true));

    const fetchHomeSummaries = async (url) => {
      try {
        const fetchHomeData = await axios.get(url);
        const resp: any = fetchHomeData.data;
        const fetchProjectCentroid = await axios.get(`${environment.baseApiUrl}/projects/centroid/`);
        const projectCentroidResp: any = fetchProjectCentroid.data;
        const addedProjectCentroidOnSummary = resp.map((project) => {
          const findProjectId = projectCentroidResp.find((payload) => payload.id === project.id);
          if (findProjectId) {
            return { ...project, centroid: findProjectId.centroid };
          }
          return project;
        });
        dispatch(HomeActions.SetHomeProjectSummary(addedProjectCentroidOnSummary));
        dispatch(HomeActions.HomeProjectLoading(false));
      } catch (error) {
        dispatch(HomeActions.HomeProjectLoading(false));
      }
    };

    await fetchHomeSummaries(url);
  };
};
export const ProjectCentroidService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(HomeActions.SetProjectCentroidLoading(true));

    const fetchProjectCentroid = async (url) => {
      try {
        const fetchHomeData = await axios.get(url);
        const resp: HomeProjectCardModel = fetchHomeData.data;

        dispatch(HomeActions.SetProjectCentroid(resp));
        dispatch(HomeActions.SetProjectCentroidLoading(false));
      } catch (error) {
        dispatch(HomeActions.SetProjectCentroidLoading(false));
      }
    };

    await fetchProjectCentroid(url);
  };
};
