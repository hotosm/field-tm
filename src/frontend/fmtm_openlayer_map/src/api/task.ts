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
                const postProjectBoundaryResponse = await CoreModules.axios.post(url);
                const response = postProjectBoundaryResponse.data;
                dispatch(CoreModules.TaskActions.PostDownloadProjectBoundary(response))
            } catch (error) {
                dispatch(CoreModules.TaskActions.PostProjectBoundaryLoading(false))
            }
        }
        await postProjectBoundaryDetails(url);
    }
}

export const fectchConvertToOsmDetails : Function = (url: string, ) => {

    return async (dispatch) => {
        dispatch(CoreModules.TaskActions.FetchConvertToOsmLoading(true))
        const fectchConvertToOsmDetail = async (url: string) => {
            try {
                const fectchConvertToOsmDetailResponse = await CoreModules.axios.get(url);
                const response = fectchConvertToOsmDetailResponse.data;
                dispatch(CoreModules.TaskActions.FetchConvertToOsm(response))
            } catch (error) {
                dispatch(CoreModules.TaskActions.FetchConvertToOsmLoading(false))
            }
        }
        await fectchConvertToOsmDetail(url);
    }
}


