import { AxiosResponse } from 'axios';
import { submissionContributorsTypes, validatedMappedType } from '@/models/submission/submissionModel';
import CoreModules from '@/shared/CoreModules';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { AppDispatch } from '@/store/Store';

export const ProjectContributorsService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const fetchProjectContributor = async (url: string) => {
      try {
        dispatch(SubmissionActions.SetSubmissionContributorsLoading(true));
        const response: AxiosResponse<submissionContributorsTypes[]> = await CoreModules.axios.get(url);
        dispatch(SubmissionActions.SetSubmissionContributors(response.data));
      } catch (error) {
      } finally {
        dispatch(SubmissionActions.SetSubmissionContributorsLoading(false));
      }
    };

    await fetchProjectContributor(url);
  };
};

export const MappedVsValidatedTaskService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const MappedVsValidatedTask = async (url: string) => {
      try {
        dispatch(SubmissionActions.SetMappedVsValidatedTaskLoading(true));
        const response: AxiosResponse<validatedMappedType[]> = await CoreModules.axios.get(url);
        dispatch(SubmissionActions.SetMappedVsValidatedTask(response.data));
        dispatch(SubmissionActions.SetMappedVsValidatedTaskLoading(false));
      } catch (error) {
        dispatch(SubmissionActions.SetMappedVsValidatedTaskLoading(false));
      }
    };

    await MappedVsValidatedTask(url);
  };
};
