import React, { useEffect } from "react";
import '../styles/home.css'
import ExploreProjectCard from "../components/home/ExploreProjectCard";
import Box from '@mui/material/Box';
import { Container, Grid, Pagination, TableRow } from "@mui/material";
import windowDimention from "../hooks/WindowDimension";
import BasicPagination from "../utilities/BasicPagination";
import { useDispatch, useSelector } from 'react-redux';
import { HomeSummaryService } from "../api/HomeService";
import enviroment from "../enviroment";
import ProjectCardSkeleton from "../components/home/ProjectCardSkeleton";
import SearchablesRow from "../components/home/HomePageFilters";


const Home = () => {


    const { type } = windowDimention();
    //get window dimension

    const dispatch = useDispatch()
    //dispatch function to perform redux state mutation

    const stateHome = useSelector((state: any) => state.home);
    //we use use selector from redux to get all state of home from home slice

    let cardsPerRow: any = new Array(type == 'xl' ? 7 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1).fill(0);
    //calculating number of cards to to display per row in order to fit our window dimension respectively and then convert it into dummy array


    useEffect(() => {
        dispatch(HomeSummaryService(`${enviroment.baseApiUrl}/projects/summaries?skip=0&limit=100`))
        //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
    }, [])

    return (
        <div style={{ padding: 7 }}>
            <SearchablesRow />
            {
                stateHome.homeProjectLoading == false ?
                    <Grid mt={2} container spacing={1} columns={{ xs: 1, sm: 3, md: 4, lg: 6, xl: 7 }}>
                        {stateHome.homeProjectSummary.map((value, index) => (
                            <Grid item xs={1} sm={1} md={1} lg={1} xl={1} key={index}>
                                <ExploreProjectCard data={value} key={index} />
                            </Grid>
                        ))}
                    </Grid>
                    : <Box sx={{ display: { xs: 'flex', sm: 'flex', md: 'flex', lg: 'flex', xl: 'flex', flexDirection: 'row', justifyContent: 'left', width: '100%' } }}>
                        <ProjectCardSkeleton cardsPerRow={cardsPerRow} />
                    </Box>

            }
            {/*pagingation*/}
            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', marginTop: '1%' }}>
                <Pagination color="standard" count={10} variant="outlined" />
            </Box>

        </div>

    )

}

export default Home;