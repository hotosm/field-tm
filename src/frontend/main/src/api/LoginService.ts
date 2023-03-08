import react from 'react';
import axios from 'axios';
import { LoginActions } from '../store/slices/LoginSlice';
import { LoginProjectCardModel } from '../models/login/loginModel';

export const LoginSummaryService: Function = (url: string) => {

    return async (dispatch) => {
        dispatch(LoginActions.LoginProjectLoading(true))

        const fetchLoginSummaries = async (url) => {

            try {
                const fetchLoginData = await axios.get(url)
                const resp: LoginProjectCardModel = fetchLoginData.data;
                // let resp = new Array(10).fill({
                //     id: 1234,
                //     priority: "MEDIUM",
                //     title: "Naivasha",
                //     location_str: "Lake Naivasha, Kenya",
                //     description: "HOT demo",
                //     total_tasks: 320,
                //     tasks_mapped: 0,
                //     tasks_validated: 0,
                //     contributors: 0,
                //     tasks_bad: 0,
                //     priority_str: 'HIGH',
                //     num_contributors: 12
                // })
                dispatch(LoginActions.SetLoginProjectSummary(resp))
                dispatch(LoginActions.LoginProjectLoading(false))
            } catch (error) {
                dispatch(LoginActions.LoginProjectLoading(false))
            }
        }

        await fetchLoginSummaries(url);

    }

}


