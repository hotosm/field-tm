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
import ProjectListMap from '../components/home/ProjectListMap';

const Home = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [paginationPage, setPaginationPage] = useState(1);

  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const showMapStatus = CoreModules.useAppSelector((state) => state.home.showMapStatus);
  const homeProjectPagination = CoreModules.useAppSelector((state) => state.home.homeProjectPagination);
  // const state:any = CoreModules.useAppSelector(state=>state.project.projectData)
  // console.log('state main :',state)

  const { type } = windowDimention();
  //get window dimension

  const dispatch = CoreModules.useAppDispatch();
  //dispatch function to perform redux state mutation

  const stateHome = CoreModules.useAppSelector((state) => state.home);
  //we use use selector from redux to get all state of home from home slice
  const filteredProjectCards = stateHome.homeProjectSummary;

  let cardsPerRow = new Array(
    type == 'xl' ? 7 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1,
  ).fill(0);
  //calculating number of cards to to display per row in order to fit our window dimension respectively and then convert it into dummy array

  const theme = CoreModules.useAppSelector((state) => state.theme.hotTheme);

  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [searchQuery, 500]);

  useEffect(() => {
    if (debouncedSearch) {
      dispatch(
        HomeSummaryService(
          `${
            import.meta.env.VITE_API_URL
          }/projects/search_projects?page=${paginationPage}&results_per_page=12&search=${debouncedSearch}`,
        ),
      );
    }
  }, [debouncedSearch, paginationPage]);

  useEffect(() => {
    setPaginationPage(1);
  }, [debouncedSearch]);

  useEffect(() => {
    if (!debouncedSearch) {
      dispatch(
        HomeSummaryService(
          `${import.meta.env.VITE_API_URL}/projects/summaries?page=${paginationPage}&results_per_page=12`,
        ),
      );
    }
  }, [paginationPage, debouncedSearch]);

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
                  <div>
                    <div
                      className={`fmtm-px-[1rem] fmtm-grid fmtm-gap-5 ${
                        !showMapStatus
                          ? 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-4 xl:fmtm-grid-cols-5 2xl:fmtm-grid-cols-6'
                          : 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-2 2xl:fmtm-grid-cols-3 lg:fmtm-h-[33rem] lg:fmtm-overflow-y-scroll lg:scrollbar'
                      }`}
                    >
                      {filteredProjectCards.map((value, index) => (
                        <ExploreProjectCard data={value} key={index} />
                      ))}
                    </div>
                  </div>
                  <div className="fmtm-flex fmtm-justify-center fmtm-mt-5">
                    <CoreModules.Pagination
                      page={homeProjectPagination?.page}
                      count={homeProjectPagination?.pages}
                      shape="rounded"
                      size={type === 'xs' ? 'small' : 'large'}
                      sx={{
                        '.Mui-selected': {
                          background: 'rgb(216,73,55) !important',
                          color: 'white',
                        },
                      }}
                      onChange={(e, page) => {
                        setPaginationPage(page);
                      }}
                    />
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
            {showMapStatus && <ProjectListMap />}
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

      {/* <div className="fmtm-flex fmtm-justify-end fmtm-mr-4 fmtm-py-1 fmtm-gap-3">
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
      </div> */}
    </div>
  );
};

export default Home;
