import axios from 'axios';
import { DataConflationActions } from '@/store/slices/DataConflationSlice';
import { AppDispatch } from '@/store/Store';

export const SubmissionConflationGeojsonService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const getSubmissionGeojsonConflation = async (url: string) => {
      try {
        dispatch(DataConflationActions.SetSubmissionConflationGeojsonLoading(true));
        const getSubmissionConflationGeojsonResponse = await axios.get(url);
        dispatch(DataConflationActions.SetSubmissionConflationGeojson(getSubmissionConflationGeojsonResponse.data));
        dispatch(DataConflationActions.SetSubmissionConflationGeojsonLoading(false));
      } catch (error) {
        dispatch(DataConflationActions.SetSubmissionConflationGeojsonLoading(false));
      }
    };

    await getSubmissionGeojsonConflation(url);
  };
};
