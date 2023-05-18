import React, { useEffect } from "react";
import '../styles/home.css'
import ExploreProjectCard from "../components/home/ExploreProjectCard";
import windowDimention from "../hooks/WindowDimension";
import { HomeSummaryService } from "../api/HomeService";
import enviroment from "../environment";
import ProjectCardSkeleton from "../components/home/ProjectCardSkeleton";
import SearchablesRow from "../components/home/HomePageFilters";
import CoreModules from "../shared/CoreModules";
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';

const Home = () => {
    
    const defaultTheme = CoreModules.useSelector(state => state.theme.hotTheme)
    // const state:any = useSelector<any>(state=>state.project.projectData)
    // console.log('state main :',state)

    const { type } = windowDimention();
    //get window dimension

    const dispatch = CoreModules.useDispatch()
    //dispatch function to perform redux state mutation

    const stateHome = CoreModules.useSelector((state) => state.home);
    //we use use selector from redux to get all state of home from home slice

    let cardsPerRow = new Array(type == 'xl' ? 7 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1).fill(0);
    //calculating number of cards to to display per row in order to fit our window dimension respectively and then convert it into dummy array

    

    const theme = CoreModules.useSelector(state => state.theme.hotTheme)
    useEffect(() => {
        dispatch(HomeSummaryService(`${enviroment.baseApiUrl}/projects/summaries?skip=0&limit=100`))
        dispatch(CreateProjectActions.SetIndividualProjectDetailsData({}));
        //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
    }, [])

    return (
        <div style={{ padding: 7 }}>
            <SearchablesRow />
            {
                stateHome.homeProjectLoading == false ?
                    <CoreModules.Grid mt={2} container spacing={1} columns={{ xs: 1, sm: 3, md: 4, lg: 6, xl: 7 }}>
                        {stateHome.homeProjectSummary.map((value, index) => (
                            <CoreModules.Grid item xs={1} sm={1} md={1} lg={1} xl={1} key={index}>
                                <ExploreProjectCard data={value} key={index} />
                            </CoreModules.Grid>
                        ))}
                    </CoreModules.Grid>
                    : <CoreModules.Stack sx={{ display: { xs: 'flex', sm: 'flex', md: 'flex', lg: 'flex', xl: 'flex', flexDirection: 'row', justifyContent: 'left', width: '100%' } }}>
                        <ProjectCardSkeleton defaultTheme={defaultTheme} cardsPerRow={cardsPerRow} />
                    </CoreModules.Stack>

            }
            {/*pagingation*/}
            {/* <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', marginTop: '1%' }}>
                <CoreModules.Pagination color="standard" count={10} variant="outlined" />
            </CoreModules.Stack> */}

        </div>

    )

}

export default Home;
