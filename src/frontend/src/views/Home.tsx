import React, { useEffect, useState } from 'react';
import '../styles/home.css';
import ExploreProjectCard from '@/components/home/ExploreProjectCard';
import windowDimention from '@/hooks/WindowDimension';
import { HomeSummaryService } from '@/api/HomeService';
import ProjectCardSkeleton from '@/components/home/ProjectCardSkeleton';
import HomePageFilters from '@/components/home/HomePageFilters';
import CoreModules from '@/shared/CoreModules';
import ProjectListMap from '@/components/home/ProjectListMap';
import { projectType } from '@/models/home/homeModel';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const Home = () => {
  useDocumentTitle('Explore Projects');
  const dispatch = useAppDispatch();
  const { type } = windowDimention();

  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [paginationPage, setPaginationPage] = useState(1);

  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);
  const showMapStatus = useAppSelector((state) => state.home.showMapStatus);
  const homeProjectPagination = useAppSelector((state) => state.home.homeProjectPagination);
  const stateHome = useAppSelector((state) => state.home);

  const filteredProjectCards = stateHome.homeProjectSummary;

  let cardsPerRow = new Array(
    type == 'xl' ? 7 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1,
  ).fill(0);

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
          }/projects/search?page=${paginationPage}&results_per_page=12&search=${debouncedSearch}`,
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
      style={{ flex: 1, background: '#F5F5F5' }}
      className="fmtm-flex fmtm-flex-col fmtm-justify-between fmtm-h-full"
    >
      <div className="fmtm-h-full">
        <HomePageFilters onSearch={handleSearch} filteredProjectCount={filteredProjectCards?.length} />
        {stateHome.homeProjectLoading == false ? (
          <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 md:fmtm-overflow-hidden lg:fmtm-h-[calc(100%-9.313rem)]">
            <div
              className={`fmtm-w-full fmtm-flex fmtm-flex-col fmtm-justify-between md:fmtm-overflow-y-scroll md:scrollbar ${showMapStatus ? 'lg:fmtm-w-[50%]' : ''} `}
            >
              {filteredProjectCards.length > 0 ? (
                <>
                  <div
                    className={`fmtm-grid fmtm-gap-5 ${
                      !showMapStatus
                        ? 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-4 xl:fmtm-grid-cols-5 2xl:fmtm-grid-cols-6'
                        : 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-2 2xl:fmtm-grid-cols-3 lg:fmtm-overflow-y-scroll lg:scrollbar'
                    }`}
                  >
                    {filteredProjectCards.map((value: projectType, index: number) => (
                      <ExploreProjectCard data={value} key={index} />
                    ))}
                  </div>
                  <div className="fmtm-flex fmtm-justify-center fmtm-mt-5 fmtm-mb-2 lg:fmtm-mb-0">
                    <CoreModules.Pagination
                      page={homeProjectPagination?.page}
                      count={homeProjectPagination?.pages}
                      shape="rounded"
                      size={type === 'xs' ? 'medium' : 'large'}
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
                </>
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
      </div>
    </div>
  );
};

export default Home;
