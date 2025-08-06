import axios from 'axios';
import { AppDispatch } from '@/store/Store';
import { HomeActions } from '@/store/slices/HomeSlice';
import { projectType } from '@/models/home/homeModel';
import { paginationType } from '@/store/types/ICommon';
import { project_status } from '@/types/enums';

export const HomeSummaryService = (
  url: string,
  params: {
    page: number;
    results_per_page?: number;
    org_id?: number;
    search?: string;
    hashtags?: string;
    minimal?: boolean;
    status?: project_status;
  },
) => {
  return async (dispatch: AppDispatch) => {
    dispatch(HomeActions.HomeProjectLoading(true));

    const fetchHomeSummaries = async () => {
      try {
        const fetchHomeData = await axios.get(url, { params });
        const projectSummaries: projectType[] = fetchHomeData.data.results;
        const paginationResp: paginationType = fetchHomeData.data.pagination;
        dispatch(HomeActions.SetHomeProjectPagination(paginationResp));
        dispatch(HomeActions.SetHomeProjectSummary(projectSummaries));
        dispatch(HomeActions.HomeProjectLoading(false));
      } catch (error) {
        dispatch(HomeActions.HomeProjectLoading(false));
      }
    };

    await fetchHomeSummaries();
  };
};
