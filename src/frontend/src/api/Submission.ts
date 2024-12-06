import axios from 'axios';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';

export const SubmissionService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(SubmissionActions.SetSubmissionDetails(null));
    dispatch(SubmissionActions.SetSubmissionDetailsLoading(true));
    const getSubmissionDetails = async (url: string) => {
      try {
        const getSubmissionDetailsResponse = await axios.get(url);
        const response: any = getSubmissionDetailsResponse.data;
        dispatch(SubmissionActions.SetSubmissionDetails(response));
        dispatch(SubmissionActions.SetSubmissionDetailsLoading(false));
      } catch (error) {
        dispatch(SubmissionActions.SetSubmissionDetailsLoading(false));
      } finally {
        dispatch(SubmissionActions.SetSubmissionDetailsLoading(false));
      }
    };
    await getSubmissionDetails(url);
  };
};

export const GetSubmissionPhotosService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(SubmissionActions.SetSubmissionPhotosLoading(true));
    const getSubmissionPhotos = async (url: string) => {
      try {
        const response = await axios.get(url);
        dispatch(SubmissionActions.SetSubmissionPhotos(response?.data?.image_urls));
        dispatch(SubmissionActions.SetSubmissionPhotosLoading(false));
      } catch (error) {
        dispatch(SubmissionActions.SetSubmissionPhotosLoading(false));
      } finally {
        dispatch(SubmissionActions.SetSubmissionPhotosLoading(false));
      }
    };
    await getSubmissionPhotos(url);
  };
};
