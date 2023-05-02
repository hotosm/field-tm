import CoreModules from 'fmtm/CoreModules';
import { ProjectActions } from 'fmtm/ProjectSlice';
// import { HomeProjectCardModel } from '../models/home/homeModel';

export const ProjectSubmissionService: Function = (url: string) => {

    return async (dispatch) => {
        dispatch(ProjectActions.GetProjectSubmissionLoading(true))

        const fetchProjectSubmission = async (url:string) => {

            try {
                const fetchSubmissionData = await CoreModules.axios.get(url)
                const resp: any = fetchSubmissionData.data;
                dispatch(ProjectActions.SetProjectSubmission(resp))
                dispatch(ProjectActions.GetProjectSubmissionLoading(false))
            } catch (error) {
                dispatch(ProjectActions.GetProjectSubmissionLoading(false))
            }
        }

        await fetchProjectSubmission(url);

    }

}
