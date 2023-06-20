import CoreModules from "fmtm/CoreModules";
import { CommonActions } from "fmtm/CommonSlice";
import { fectchConvertToOsmDetail } from './task';


export const fetchInfoTask: Function = (url: string) => {
    return async (dispatch) => {
        dispatch(CoreModules.TaskActions.SetTaskLoading(true))
        dispatch(CommonActions.SetLoading(true))
        const fetchTaskInfoDetails = async (url: string) => {
            try {
                const fetchTaskInfoDetailsResponse = await CoreModules.axios.get(url);
                const response = fetchTaskInfoDetailsResponse.data;
                dispatch(CommonActions.SetLoading(false))
                dispatch(CoreModules.TaskActions.FetchTaskInfoDetails(response))
            } catch (error) {
                dispatch(CommonActions.SetLoading(false))
                dispatch(CoreModules.TaskActions.SetTaskLoading(false))
            }
        }
        await fetchTaskInfoDetails(url);
    }
}


export const postDownloadProjectBoundary : Function = (url: string, ) => {

    return async (dispatch) => {
        dispatch(CoreModules.TaskActions.PostProjectBoundaryLoading(true))
        const postProjectBoundaryDetails = async (url: string) => {
            try {
                const response = await CoreModules.axios.post(url, null, {
                    headers: {
                    'Content-Type': 'application/json',
                  },
                  responseType : 'blob',
                });
                console.log(response
                    , 'response');

                const downloadLink = document.createElement('a');
                downloadLink.href = window.URL.createObjectURL(new Blob([response]));
                downloadLink.setAttribute('download', 'download.zip');
                document.body.appendChild(downloadLink);

                downloadLink.click();

                document.body.removeChild(downloadLink);
                window.URL.revokeObjectURL(downloadLink.href);

                dispatch(CoreModules.TaskActions.PostDownloadProjectBoundary(response))
            } catch (error) {
                dispatch(CoreModules.TaskActions.PostProjectBoundaryLoading(false))
            }
        }
        await postProjectBoundaryDetails(url);
    }
}

export const fetchConvertToOsmDetails: Function = (url: string) => {
    return async (dispatch) => {
      dispatch(CoreModules.TaskActions.FetchConvertToOsmLoading(true));
  
      try {
        const response = await CoreModules.axios.get(url, { responseType: 'blob' });
  
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
  


