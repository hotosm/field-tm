import axios from 'axios';
import { AppDispatch } from '@/store/Store';
import { HomeActions } from '@/store/slices/HomeSlice';
import { projectType } from '@/models/home/homeModel';
import { paginationType } from '@/store/types/ICommon';

export const HomeSummaryService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    dispatch(HomeActions.HomeProjectLoading(true));

    const fetchHomeSummaries = async (url: string) => {
      try {
        const fetchHomeData = await axios.get(url);
        const projectSummaries: projectType[] = fetchHomeData.data.results;
        const paginationResp: paginationType = fetchHomeData.data.pagination;
        dispatch(HomeActions.SetHomeProjectPagination(paginationResp));
        dispatch(HomeActions.SetHomeProjectSummary(projectSummaries));
        dispatch(HomeActions.HomeProjectLoading(false));
      } catch (error) {
        dispatch(HomeActions.HomeProjectLoading(false));
      }
    };

    await fetchHomeSummaries(url);
  };
};
