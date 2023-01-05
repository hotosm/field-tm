import React, { useEffect } from "react";
import ExploreProjectCard from "../components/home/ExploreProjectCard";
import Box from '@mui/material/Box';
import { Container, TableRow } from "@mui/material";
import windowDimention from "../customHooks/WindowDimension";
import BasicPagination from "../utilities/BasicPagination";
import { useDispatch, useSelector } from 'react-redux';
import { HomeSummaryService } from "../services/HomeService";
import enviroment from "../enviroment";
import ProjectCardSkeleton from "../components/home/ProjectCardSkeleton";


const Home = () => {


    const { windowSize, type } = windowDimention();

    //get window dimension

    const dispatch = useDispatch()
    //dispatch function to perform redux state mutation

    const stateHome = useSelector((state: any) => state.home);
    //we use use selector from redux to get all state of home from home slice

    let projectSummaryData = [...stateHome.homeProjectSummary];
    // initialization of new project data array for further manipulations


    let cardsPerRow: any = new Array(type == 'xl' ? 7 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1).fill(0);
    //calculating number of cards to to display per row in order to fit our window dimension respectively and then convert it into dummy array


    let totalRows: any = new Array(stateHome.homeProjectSummary.length % cardsPerRow.length == 0 ? Math.floor(stateHome.homeProjectSummary.length / cardsPerRow.length) : Math.floor(stateHome.homeProjectSummary.length / cardsPerRow.length) + 1).fill(0)
    //calculating number of rows that current displayed list will fit in respectively and then convert it into dummy array




    useEffect(() => {
        dispatch(HomeSummaryService(`${enviroment.baseApiUrl}/projects/summaries?skip=0&limit=100`))
        //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
    }, [])

    return (
        <div style={{ padding: 7 }}>
            {
                stateHome.homeProjectLoading == false ?
                    //making sure we only want to start to display data when actually have data
                    totalRows.map((value, index) => {
                        //displaying rows to handle our cards
                        return (
                            <Box key={index} sx={{ display: { xs: 'flex', sm: 'flex', md: 'flex', lg: 'flex', xl: 'flex', flexDirection: 'row', justifyContent: 'left', width: '100%', } }}>
                                {/* defining rows properties */}
                                {
                                    stateHome.homeProjectSummary.length % cardsPerRow.length == 0 ?
                                        //checking if project list fit a defined row

                                        cardsPerRow.map((val, index) => {
                                            //displaying cards on every give row

                                            let value = projectSummaryData.shift()
                                            //manipulating the new project array, capture current last index value, displaying it then remove it from the array 
                                            return (
                                                <ExploreProjectCard data={value} length={cardsPerRow.length} key={index} />
                                            )
                                        }) :


                                        //if false the we expect that there will be a reminder in our list that doesn't fit in given.
                                        //eg: list of 10 / 7 as window dimention of xl to fit our cards respectively then the reminder will be 3 which should be render in the last row
                                        index + 1 != totalRows.length ?

                                            //checking if is not the last irritation we don't focus on the reminder
                                            cardsPerRow.map((val, index) => {

                                                let value = projectSummaryData.shift()
                                                return (
                                                    <ExploreProjectCard data={value} length={cardsPerRow.length} key={index} />
                                                )
                                            }) :
                                            //if is the last row then we dont want to loop down the card more then the reminder
                                            // so if 3 is a reminder we only want 3 irritation to finish the last row
                                            new Array(stateHome.homeProjectSummary.length % cardsPerRow.length).fill(0).map((val, index) => {

                                                //getting the reminder and convert it in a dummy array to get a respective loop
                                                let value = projectSummaryData.shift()

                                                return (
                                                    <ExploreProjectCard length={cardsPerRow.length} data={value} key={index} />
                                                )
                                            })
                                }
                            </Box>
                        )

                    })
                    //IF no data loaded then we perform skeleton loading
                    : <Box sx={{ display: { xs: 'flex', sm: 'flex', md: 'flex', lg: 'flex', xl: 'flex', flexDirection: 'row', justifyContent: 'left', width: '100%' } }}>
                        <ProjectCardSkeleton cardsPerRow={cardsPerRow} />
                    </Box>

            }
            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', marginTop: '1%' }}>
                <BasicPagination count={10} color="primary" variant="outlined" />
            </Box>
            {/*pagingation*/}

        </div>

    )

}

export default Home;