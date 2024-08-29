import axios from 'axios';
import { DataConflationActions } from '@/store/slices/DataConflationSlice';

export const SubmissionConflationGeojsonService: Function = (url: string) => {
  return async (dispatch) => {
    const getSubmissionGeojsonConflation = async (url) => {
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
