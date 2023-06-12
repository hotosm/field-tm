import CoreModules from "fmtm/CoreModules";

export const fetchInfoTask: Function = (url: string) => {
    return async (dispatch) => {
        dispatch(CoreModules.TaskActions.SetTaskLoading(true))
        const fetchTaskInfoDetails = async (url:string) => {
            try {
                const fetchTaskInfoDetailsResponse = await CoreModules.axios.get(url);
                const response = fetchTaskInfoDetailsResponse.data;
                dispatch(CoreModules.TaskActions.FetchTaskInfoDetails(response))
            } catch (error) {
                dispatch(CoreModules.TaskActions.SetTaskLoading(false))
            }
        }
        await fetchTaskInfoDetails(url);
    }
}