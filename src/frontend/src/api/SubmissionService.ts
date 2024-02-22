import CoreModules from '@/shared/CoreModules';
import { ProjectActions } from '@/store/slices/ProjectSlice';
// import { HomeProjectCardModel } from '@/models/home/homeModel';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { basicGeojsonTemplate } from '@/utilities/mapUtils';

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

export const ProjectSubmissionInfographicsService: Function = (url: string) => {
  return async (dispatch) => {
    const fetchProjectSubmission = async (url: string) => {
      try {
        dispatch(SubmissionActions.SetSubmissionInfographicsLoading(true));
        const fetchSubmissionData = await CoreModules.axios.get(url);
        const resp: any = fetchSubmissionData.data;
        dispatch(SubmissionActions.SetSubmissionInfographicsLoading(false));
        dispatch(SubmissionActions.SetSubmissionInfographics(resp));
      } catch (error) {}
    };

    await fetchProjectSubmission(url);
  };
};

export const ValidatedVsMappedInfographicsService: Function = (url: string) => {
  return async (dispatch) => {
    const fetchProjectSubmission = async (url: string) => {
      try {
        dispatch(SubmissionActions.SetValidatedVsMappedLoading(true));
        const validatedVsMappedData = await CoreModules.axios.get(url);
        const resp: any = validatedVsMappedData.data;
        dispatch(SubmissionActions.SetValidatedVsMappedInfographics(resp));
        dispatch(SubmissionActions.SetValidatedVsMappedLoading(false));
      } catch (error) {
        dispatch(SubmissionActions.SetValidatedVsMappedLoading(false));
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

export const SubmissionTableService: Function = (url: string, payload) => {
  return async (dispatch) => {
    const fetchSubmissionTable = async (url: string, payload) => {
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
