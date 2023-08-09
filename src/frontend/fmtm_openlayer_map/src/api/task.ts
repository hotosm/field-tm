import CoreModules from "fmtm/CoreModules";
import { CommonActions } from "fmtm/CommonSlice";

export const fetchInfoTask: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CoreModules.TaskActions.SetTaskLoading(true));
    dispatch(CommonActions.SetLoading(true));
    const fetchTaskInfoDetails = async (url: string) => {
      try {
        const fetchTaskInfoDetailsResponse = await CoreModules.axios.get(url);
        const response = fetchTaskInfoDetailsResponse.data;
        dispatch(CommonActions.SetLoading(false));
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
    const params = new URLSearchParams(url.split("?")[1]);
    const isExportJson = params.get("export_json");
    const isJsonOrCsv = isExportJson === "true" ? "json" : "csv";
    dispatch(
      CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
        type: isJsonOrCsv,
        loading: true,
      })
    );

    const getProjectSubmission = async (url: string) => {
      try {
        const response = await CoreModules.axios.get(url, {
          responseType: "blob",
        });
        var a = document.createElement("a");
        a.href = window.URL.createObjectURL(response.data);
        a.download = "Submissions";
        a.click();
        dispatch(
          CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
            type: isJsonOrCsv,
            loading: false,
          })
        );
      } catch (error) {
        dispatch(
          CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
            type: isJsonOrCsv,
            loading: false,
          })
        );
      } finally {
        dispatch(
          CoreModules.TaskActions.GetDownloadProjectSubmissionLoading({
            type: isJsonOrCsv,
            loading: false,
          })
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
        responseType: "blob",
      });

      const downloadLink = document.createElement("a");
      downloadLink.href = window.URL.createObjectURL(new Blob([response.data]));
      downloadLink.setAttribute("download", "task.zip");
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

export const ConvertXMLToJOSM: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CoreModules.TaskActions.SetConvertXMLToJOSMLoading(true));
    const getConvertXMLToJOSM = async (url) => {
      try {
        const params = {
          url: url,
        };
        // checkJOSMOpen - To check if JOSM Editor is Open Or Not.
        await CoreModules.axios.get(
          `http://127.0.0.1:8111/version?jsonp=checkJOSM`
        );
        //importToJosmEditor - To open JOSM Editor and add XML of Project Submission To JOSM.

        CoreModules.axios.get(
          `http://127.0.0.1:8111/imagery?title=osm&type=tms&url=https://tile.openstreetmap.org/%7Bzoom%7D/%7Bx%7D/%7By%7D.png`
          //   `http://127.0.0.1:8111/imagery?title=osm&type=tms&min_zoom=4&max_zoom=14&url=https://tile.openstreetmap.org/%7Bzoom%7D/%7Bx%7D/%7By%7D.png`
        );
        await CoreModules.axios.get(`http://127.0.0.1:8111/import?url=${url}`);
        // const getConvertXMLToJOSMResponse = await CoreModules.axios.get(url);
        // const response: any = getConvertXMLToJOSMResponse.data;

        // dispatch(CoreModules.TaskActions.SetConvertXMLToJOSMLoading(response[0].value[0]));
      } catch (error: any) {
        dispatch(CoreModules.TaskActions.SetJosmEditorError("JOSM Error"));
        // alert(error.response.data);
        dispatch(CoreModules.TaskActions.SetConvertXMLToJOSMLoading(false));
      } finally {
        dispatch(CoreModules.TaskActions.SetConvertXMLToJOSMLoading(false));
      }
    };
    await getConvertXMLToJOSM(url);
  };
};
