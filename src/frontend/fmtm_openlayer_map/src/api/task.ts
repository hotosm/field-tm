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


export const getDownloadProjectBoundary : Function = (url: string, ) => {

    return async (dispatch) => {
        dispatch(CoreModules.TaskActions.GetProjectBoundaryLoading(true))
        const getProjectBoundaryDetails = async (url: string) => {
            try {
                const response = await CoreModules.axios.get(url, {
                  responseType : 'blob',
                });

                const downloadLink = document.createElement('a');
                downloadLink.href = window.URL.createObjectURL(new Blob([response.data]));
                downloadLink.setAttribute('download', 'download.zip');
                document.body.appendChild(downloadLink);

                downloadLink.click();

                document.body.removeChild(downloadLink);
                window.URL.revokeObjectURL(downloadLink.href);

                dispatch(CoreModules.TaskActions.GetDownloadProjectBoundary(response.data))
            } catch (error) {
                dispatch(CoreModules.TaskActions.GetProjectBoundaryLoading(false))
            }
        }
        await getProjectBoundaryDetails(url);
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
  


