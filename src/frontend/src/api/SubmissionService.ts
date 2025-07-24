import { AxiosResponse } from 'axios';
import {
  submissionContributorsTypes,
  submissionFormFieldsTypes,
  submissionTableDataTypes,
  updateReviewStateType,
  validatedMappedType,
} from '@/models/submission/submissionModel';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { filterType } from '@/store/types/ISubmissions';
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

export const SubmissionFormFieldsService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const fetchFormFields = async (url: string) => {
      try {
        dispatch(SubmissionActions.SetSubmissionFormFieldsLoading(true));
        const response: AxiosResponse<submissionFormFieldsTypes[]> = await CoreModules.axios.get(url);
        dispatch(SubmissionActions.SetSubmissionFormFields(response.data));
        dispatch(SubmissionActions.SetSubmissionFormFieldsLoading(false));
        dispatch(SubmissionActions.SetSubmissionTableRefreshing(false));
      } catch (error) {
        dispatch(SubmissionActions.SetSubmissionFormFieldsLoading(false));
        dispatch(SubmissionActions.SetSubmissionTableRefreshing(false));
      }
    };

    await fetchFormFields(url);
  };
};

export const SubmissionTableService = (url: string, payload: filterType) => {
  return async (dispatch: AppDispatch) => {
    const fetchSubmissionTable = async (url: string, payload: filterType) => {
      try {
        dispatch(SubmissionActions.SetSubmissionTableLoading(true));
        const response: AxiosResponse<submissionTableDataTypes> = await CoreModules.axios.get(url, { params: payload });
        dispatch(SubmissionActions.SetSubmissionTable(response.data));
        dispatch(SubmissionActions.SetSubmissionTableLoading(false));
        dispatch(SubmissionActions.SetSubmissionTableRefreshing(false));
      } catch (error) {
        dispatch(SubmissionActions.SetSubmissionTableLoading(false));
        dispatch(SubmissionActions.SetSubmissionTableRefreshing(false));
      }
    };

    await fetchSubmissionTable(url, payload);
  };
};

export const UpdateReviewStateService = (url: string, payload: object) => {
  return async (dispatch: AppDispatch) => {
    const UpdateReviewState = async (url: string) => {
      try {
        dispatch(SubmissionActions.UpdateReviewStateLoading(true));
        const response: AxiosResponse<updateReviewStateType> = await CoreModules.axios.post(url, payload);
        dispatch(SubmissionActions.UpdateSubmissionTableDataReview(response.data));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Failed to update review state.',
          }),
        );
        dispatch(SubmissionActions.UpdateReviewStateLoading(false));
      }
    };

    await UpdateReviewState(url);
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
