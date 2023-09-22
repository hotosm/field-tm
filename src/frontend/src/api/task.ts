import CoreModules from '../shared/CoreModules';
import { CommonActions } from '../store/slices/CommonSlice';

export const fetchInfoTask: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CoreModules.TaskActions.SetTaskLoading(true));
    dispatch(CommonActions.SetLoading(true));
    const fetchTaskInfoDetails = async (url: string) => {
      try {
        const fetchTaskInfoDetailsResponse = await CoreModules.axios.get(url);
        const response = fetchTaskInfoDetailsResponse.data;
        dispatch(CommonActions.SetLoading(false));
        dispatch(CoreModules.TaskActions.SetTaskLoading(false));
        dispatch(CoreModules.TaskActions.FetchTaskInfoDetails(response));
      } catch (error) {
        dispatch(CommonActions.SetLoading(false));
        dispatch(CoreModules.TaskActions.SetTaskLoading(false));
      }
    };
    await fetchTaskInfoDetails(url);
  };
};

export const getDownloadProjectSubmission: Function = (url: string) => {
  return async (dispatch) => {
    const params = new URLSearchParams(url.split('?')[1]);
    const isExportJson = params.get('export_json');
    const isJsonOrCsv = isExportJson === 'true' ? 'json' : 'csv';
    dispatch(
      CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
        type: isJsonOrCsv,
        loading: true,
      }),
    );

    const getProjectSubmission = async (url: string) => {
      try {
        const response = await CoreModules.axios.get(url, {
          responseType: 'blob',
        });
        var a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = 'Submissions';
        a.click();
        dispatch(
          CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
            type: isJsonOrCsv,
            loading: false,
          }),
        );
      } catch (error) {
        dispatch(
          CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
            type: isJsonOrCsv,
            loading: false,
          }),
        );
      } finally {
        dispatch(
          CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
            type: isJsonOrCsv,
            loading: false,
          }),
        );
      }
    };
    await getProjectSubmission(url);
  };
};

export const fetchConvertToOsmDetails: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CoreModules.TaskActions.FetchConvertToOsmLoading(true));

    try {
      const response = await CoreModules.axios.get(url, {
        responseType: 'blob',
      });

      const downloadLink = document.createElement('a');
      downloadLink.href = window.URL.createObjectURL(new Blob([response.data]));
      downloadLink.setAttribute('download', 'task.zip');
      document.body.appendChild(downloadLink);

      downloadLink.click();

      document.body.removeChild(downloadLink);
      window.URL.revokeObjectURL(downloadLink.href);

      dispatch(CoreModules.TaskActions.FetchConvertToOsm(response.data));
    } catch (error) {
      dispatch(CoreModules.TaskActions.FetchConvertToOsmLoading(false));
    }
  };
};

export const ConvertXMLToJOSM: Function = (url: string, projectBbox) => {
  return async (dispatch) => {
    dispatch(CoreModules.TaskActions.SetConvertXMLToJOSMLoading(true));
    const getConvertXMLToJOSM = async (url) => {
      try {
        // checkJOSMOpen - To check if JOSM Editor is Open Or Not.
        await CoreModules.axios.get(`http://127.0.0.1:8111/version?jsonp=checkJOSM`);
        //importToJosmEditor - To open JOSM Editor and add XML of Project Submission To JOSM.
        CoreModules.axios.get(
          `http://127.0.0.1:8111/imagery?title=osm&type=tms&url=https://tile.openstreetmap.org/%7Bzoom%7D/%7Bx%7D/%7By%7D.png`,
        );
        await CoreModules.axios.get(`http://127.0.0.1:8111/import?url=${url}`);
        // `http://127.0.0.1:8111/load_and_zoom?left=80.0580&right=88.2015&top=27.9268&bottom=26.3470`;

        const loadAndZoomParams = {
          left: projectBbox[0],
          bottom: projectBbox[1],
          right: projectBbox[2],
          top: projectBbox[3],
          changeset_comment: 'fmtm',
          // changeset_source: project.imagery ? project.imagery : '',
          new_layer: 'true',
          layer_name: 'OSM Data',
        };
        await CoreModules.axios.get(`http://127.0.0.1:8111/zoom`, {
          params: loadAndZoomParams,
        });
      } catch (error: any) {
        dispatch(CoreModules.TaskActions.SetJosmEditorError('JOSM Error'));
        // alert(error.response.data);
        dispatch(CoreModules.TaskActions.SetConvertXMLToJOSMLoading(false));
      } finally {
        dispatch(CoreModules.TaskActions.SetConvertXMLToJOSMLoading(false));
      }
    };
    await getConvertXMLToJOSM(url);
  };
};
