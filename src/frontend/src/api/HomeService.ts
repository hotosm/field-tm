import axios from 'axios';
import { HomeActions } from '@/store/slices/HomeSlice';

export const HomeSummaryService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(HomeActions.HomeProjectLoading(true));

    const fetchHomeSummaries = async (url: string) => {
      try {
        const fetchHomeData = await axios.get(url);
        const projectSummaries: any = fetchHomeData.data.results;
        const paginationResp = fetchHomeData.data.pagination;
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
