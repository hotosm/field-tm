import CoreModules from "fmtm/CoreModules";
import { CommonActions } from "fmtm/CommonSlice";


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