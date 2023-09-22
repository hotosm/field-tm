import axios from 'axios';
import { SubmissionActions } from '../store/slices/SubmissionSlice';

export const SubmissionService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(SubmissionActions.SetSubmissionDetailsLoading(true));
    const getSubmissionDetails = async (url) => {
      try {
        const getSubmissionDetailsResponse = await axios.get(url);
        const response: any = getSubmissionDetailsResponse.data;
        dispatch(SubmissionActions.SetSubmissionDetails(response[0].value[0]));
      } catch (error) {
        dispatch(SubmissionActions.SetSubmissionDetailsLoading(false));
      } finally {
        dispatch(SubmissionActions.SetSubmissionDetailsLoading(false));
      }
    };
    await getSubmissionDetails(url);
  };
};
