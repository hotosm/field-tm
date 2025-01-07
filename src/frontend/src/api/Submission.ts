import axios, { AxiosResponse } from 'axios';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';

export const SubmissionService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(SubmissionActions.SetSubmissionDetails(null));
    dispatch(SubmissionActions.SetSubmissionDetailsLoading(true));
    const getSubmissionDetails = async (url: string) => {
      try {
        const response: AxiosResponse<Record<string, any>> = await axios.get(url);
        dispatch(SubmissionActions.SetSubmissionDetails(response.data));
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
        const response: AxiosResponse<{ image_urls: string[] }> = await axios.get(url);
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
