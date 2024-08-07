import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { filterType } from '@/store/types/ISubmissions';

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

export const ProjectContributorsService: Function = (url: string) => {
  return async (dispatch) => {
    const fetchProjectContributor = async (url: string) => {
      try {
        dispatch(SubmissionActions.SetSubmissionContributorsLoading(true));
        const fetchContributorsData = await CoreModules.axios.get(url);
        const resp: any = fetchContributorsData.data;
        dispatch(SubmissionActions.SetSubmissionContributors(resp));
        dispatch(SubmissionActions.SetSubmissionContributorsLoading(false));
      } catch (error) {
        dispatch(SubmissionActions.SetSubmissionContributorsLoading(false));
      }
    };

    await fetchProjectContributor(url);
  };
};

export const SubmissionFormFieldsService: Function = (url: string) => {
  return async (dispatch) => {
    const fetchFormFields = async (url: string) => {
      try {
        dispatch(SubmissionActions.SetSubmissionFormFieldsLoading(true));
        const response = await CoreModules.axios.get(url);
        const formFields: any = response.data;
        dispatch(SubmissionActions.SetSubmissionFormFields(formFields));
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

export const SubmissionTableService: Function = (url: string, payload: filterType) => {
  return async (dispatch) => {
    const fetchSubmissionTable = async (url: string, payload: filterType) => {
      try {
        dispatch(SubmissionActions.SetSubmissionTableLoading(true));
        const response = await CoreModules.axios.get(url, { params: payload });
        const submissionTableData: any = response.data;
        dispatch(SubmissionActions.SetSubmissionTable(submissionTableData));
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

export const UpdateReviewStateService: Function = (url: string) => {
  return async (dispatch) => {
    const UpdateReviewState = async (url: string) => {
      try {
        dispatch(SubmissionActions.UpdateReviewStateLoading(true));
        const response = await CoreModules.axios.post(url);
        dispatch(SubmissionActions.UpdateSubmissionTableDataReview(response.data));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Failed to update review state.',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(SubmissionActions.UpdateReviewStateLoading(false));
      }
    };

    await UpdateReviewState(url);
  };
};
