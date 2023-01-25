import react from 'react';
import axios from 'axios';
import { HomeActions } from '../store/slices/HomeSlice';
import { HomeProjectCardModel } from '../models/home/homeModel';

export const HomeSummaryService: Function = (url: string) => {

    return async (dispatch) => {
        dispatch(HomeActions.HomeProjectLoading(true))

        const fetchHomeSummaries = async (url) => {

            const fetchHomeData = await axios.get(url)
            const resp: HomeProjectCardModel = fetchHomeData.data;


            dispatch(HomeActions.SetHomeProjectSummary(resp))
            dispatch(HomeActions.HomeProjectLoading(false))
        }

        fetchHomeSummaries(url);

    }

}

