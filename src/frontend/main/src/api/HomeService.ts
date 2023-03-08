import react from 'react';
import axios from 'axios';
import { HomeActions } from '../store/slices/HomeSlice';
import { HomeProjectCardModel } from '../models/home/homeModel';

export const HomeSummaryService: Function = (url: string) => {

    return async (dispatch) => {
        dispatch(HomeActions.HomeProjectLoading(true))

        const fetchHomeSummaries = async (url) => {

            try {
                const fetchHomeData = await axios.get(url)
                const resp: HomeProjectCardModel = fetchHomeData.data;
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
                dispatch(HomeActions.SetHomeProjectSummary(resp))
                dispatch(HomeActions.HomeProjectLoading(false))
            } catch (error) {
                dispatch(HomeActions.HomeProjectLoading(false))
            }
        }

        await fetchHomeSummaries(url);

    }

}


