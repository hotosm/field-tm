import React, { useEffect, useState } from 'react';
import '../styles/home.css';
import ExploreProjectCard from '../components/home/ExploreProjectCard';
import windowDimention from '../hooks/WindowDimension';
import { HomeSummaryService } from '../api/HomeService';
import enviroment from '../environment';
import ProjectCardSkeleton from '../components/home/ProjectCardSkeleton';
import HomePageFilters from '../components/home/HomePageFilters';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';

const Home = () => {
  const [searchQuery, setSearchQuery] = useState('');

  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const showMapStatus = CoreModules.useAppSelector((state) => state.home.showMapStatus);
  // const state:any = CoreModules.useAppSelector(state=>state.project.projectData)
  // console.log('state main :',state)

  const { type } = windowDimention();
  //get window dimension

  const dispatch = CoreModules.useAppDispatch();
  //dispatch function to perform redux state mutation

  const stateHome = CoreModules.useAppSelector((state) => state.home);
  //we use use selector from redux to get all state of home from home slice

  let cardsPerRow = new Array(
    type == 'xl' ? 7 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1,
  ).fill(0);
  //calculating number of cards to to display per row in order to fit our window dimension respectively and then convert it into dummy array

  const theme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  useEffect(() => {
    dispatch(HomeSummaryService(`${enviroment.baseApiUrl}/projects/summaries?skip=0&limit=100`));
    //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
  }, []);

  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  const filteredProjectCards = stateHome.homeProjectSummary.filter((value) =>
    value.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div
      style={{ padding: 7, flex: 1, background: '#F5F5F5' }}
      className="fmtm-flex fmtm-flex-col fmtm-justify-between"
    >
      <div>
        <HomePageFilters
          onSearch={handleSearch}
          filteredProjectCount={filteredProjectCards?.length}
          totalProjectCount={stateHome.homeProjectSummary.length}
        />
        {stateHome.homeProjectLoading == false ? (
          <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5">
            <div className={`fmtm-w-full ${showMapStatus ? 'lg:fmtm-w-[50%]' : ''} `}>
              {filteredProjectCards.length > 0 ? (
                <div>
                  <div
                    className={`fmtm-px-[1rem] fmtm-grid fmtm-gap-5 ${
                      !showMapStatus
                        ? 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-4 xl:fmtm-grid-cols-5 2xl:fmtm-grid-cols-6'
                        : 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-2 2xl:fmtm-grid-cols-3 lg:fmtm-h-[33rem] lg:fmtm-overflow-y-scroll lg:scrollbar fmtm-pr-1'
                    }`}
                  >
                    {filteredProjectCards.map((value, index) => (
                      <ExploreProjectCard data={value} key={index} />
                    ))}
                  </div>
                </div>
              ) : (
                <CoreModules.Typography
                  variant="h2"
                  color="error"
                  sx={{ p: 2, textAlign: 'center' }}
                  className="fmtm-h-full fmtm-flex fmtm-justify-center fmtm-items-center"
                >
                  No projects found.
                </CoreModules.Typography>
              )}
            </div>
            {showMapStatus && (
              <div className="lg:fmtm-w-[50%] fmtm-h-[33rem] fmtm-bg-gray-300 fmtm-mx-4 fmtm-mb-2"></div>
            )}
          </div>
        ) : (
          <CoreModules.Stack
            sx={{
              display: {
                xs: 'flex',
                sm: 'flex',
                md: 'flex',
                lg: 'flex',
                xl: 'flex',
                flexDirection: 'row',
                justifyContent: 'left',
                width: '100%',
              },
            }}
          >
            <ProjectCardSkeleton defaultTheme={defaultTheme} cardsPerRow={cardsPerRow} />
          </CoreModules.Stack>
        )}
        {/*pagingation*/}
        {/* <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', marginTop: '1%' }}>
        <CoreModules.Pagination color="standard" count={10} variant="outlined" />
      </CoreModules.Stack> */}
      </div>

      <div className="fmtm-flex fmtm-justify-end fmtm-mr-4 fmtm-py-1 fmtm-gap-3">
        <div>1-5 of 10 </div>
        <AssetModules.ArrowLeftIcon
          sx={{
            fontSize: 25,
            color: '#555555',
            cursor: 'pointer',
          }}
        />
        <AssetModules.ArrowRightIcon
          sx={{
            fontSize: 25,
            color: '#555555',
            cursor: 'pointer',
          }}
        />
        <div>Jump to</div>
        <input
          type="number"
          className="fmtm-w-10 fmtm-rounded-md fmtm-border-[1px] fmtm-border-[#E7E2E2] fmtm-outline-none"
        />
      </div>
    </div>
  );
};

export default Home;
