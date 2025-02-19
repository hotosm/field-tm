import { AppDispatch } from '@/store/Store';
import CoreModules from '@/shared/CoreModules';
import { TaskActions } from '@/store/slices/TaskSlice';
import { CommonActions } from '@/store/slices/CommonSlice';

export const DownloadProjectSubmission = (
  url: string,
  projectName: string,
  params: { project_id: string; file_type: 'csv' | 'json' | 'geojson'; submitted_date_range: string | null },
) => {
  return async (dispatch: AppDispatch) => {
    dispatch(
      TaskActions.DownloadProjectSubmissionLoading({
        fileType: params.file_type,
        loading: true,
      }),
    );

    const getProjectSubmission = async (url: string) => {
      try {
        const response = await CoreModules.axios.get(url, { params, responseType: 'blob' });
        var a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        // CSV format is actually zipped, so change extension
        a.download = `${projectName}.${params.file_type === 'csv' ? 'zip' : params.file_type}`;
        a.click();
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: JSON.parse(await error?.response?.data?.text())?.detail || 'Failed to download submissions',
          }),
        );
      } finally {
        dispatch(
          TaskActions.DownloadProjectSubmissionLoading({
            fileType: params.file_type,
            loading: false,
          }),
        );
      }
    };
    await getProjectSubmission(url);
  };
};

export const ConvertXMLToJOSM = (url: string, projectBbox: number[]) => {
  return async (dispatch: AppDispatch) => {
    dispatch(TaskActions.SetConvertXMLToJOSMLoading(true));
    const getConvertXMLToJOSM = async (url) => {
      try {
        // checkJOSMOpen - To check if JOSM Editor is Open Or Not.
        await fetch(`http://127.0.0.1:8111/version?jsonp=checkJOSM`);
        //importToJosmEditor - To open JOSM Editor and add base layer To JOSM.
        fetch(
          `http://127.0.0.1:8111/imagery?title=osm&type=tms&url=https://tile.openstreetmap.org/%7Bzoom%7D/%7Bx%7D/%7By%7D.png`,
        );
        await fetch(`http://127.0.0.1:8111/import?url=${url}`);
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
        const queryString = Object.keys(loadAndZoomParams)
          .map((key) => key + '=' + loadAndZoomParams[key])
          .join('&');

        await fetch(`http://127.0.0.1:8111/zoom?${queryString}`);
      } catch (error: any) {
        dispatch(TaskActions.SetJosmEditorError('JOSM Error'));
      } finally {
        dispatch(TaskActions.SetConvertXMLToJOSMLoading(false));
      }
    };
    await getConvertXMLToJOSM(url);
  };
};
