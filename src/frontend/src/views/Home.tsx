import React, { useEffect, useState } from 'react';
import '../styles/home.css';
import ExploreProjectCard from '@/components/home/ExploreProjectCard';
import { HomeSummaryService } from '@/api/HomeService';
import ProjectCardSkeleton from '@/components/home/ProjectCardSkeleton';
import HomePageFilters from '@/components/home/HomePageFilters';
import ProjectListMap from '@/components/home/ProjectListMap';
import { projectType } from '@/models/home/homeModel';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import Pagination from '@/components/common/Pagination';
import useDebouncedInput from '@/hooks/useDebouncedInput';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const Home = () => {
  useDocumentTitle('Explore Projects');
  const dispatch = useAppDispatch();

  const [searchQuery, setSearchQuery] = useState('');
  const [paginationPage, setPaginationPage] = useState(1);

  const showMapStatus = useAppSelector((state) => state.home.showMapStatus);
  const homeProjectPagination = useAppSelector((state) => state.home.homeProjectPagination);
  const stateHome = useAppSelector((state) => state.home);
  const filteredProjectCards = stateHome.homeProjectSummary;

  const [searchTextData, handleChangeData] = useDebouncedInput({
    ms: 400,
    init: searchQuery,
    onChange: (e) => {
      setSearchQuery(e.target.value);
    },
  });

  useEffect(() => {
    dispatch(
      HomeSummaryService(
        `${VITE_API_URL}/projects/search?page=${paginationPage}&results_per_page=12&search=${searchQuery}`,
      ),
    );
  }, [searchQuery, paginationPage]);

  useEffect(() => {
    setPaginationPage(1);
  }, [searchQuery]);

  return (
    <div
      style={{ flex: 1, background: '#F5F5F5' }}
      className="fmtm-flex fmtm-flex-col fmtm-justify-between fmtm-h-full lg:fmtm-overflow-hidden"
    >
      <div className="fmtm-h-full">
        <HomePageFilters searchText={searchTextData} onSearch={handleChangeData} />
        {!stateHome.homeProjectLoading ? (
          <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 fmtm-mt-2 md:fmtm-overflow-hidden lg:fmtm-h-[calc(100%-85px)] fmtm-pb-16 lg:fmtm-pb-0">
            <div
              className={`fmtm-w-full fmtm-flex fmtm-flex-col fmtm-justify-between md:fmtm-overflow-y-scroll md:scrollbar ${showMapStatus ? 'lg:fmtm-w-[50%]' : ''} `}
            >
              {filteredProjectCards.length > 0 ? (
                <>
                  <div
                    className={`fmtm-grid fmtm-gap-3 ${
                      !showMapStatus
                        ? 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-4 xl:fmtm-grid-cols-5 2xl:fmtm-grid-cols-6'
                        : 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-2 2xl:fmtm-grid-cols-3 lg:fmtm-overflow-y-scroll lg:scrollbar'
                    }`}
                  >
                    {filteredProjectCards.map((value: projectType, index: number) => (
                      <ExploreProjectCard data={value} key={index} />
                    ))}
                  </div>
                </>
              ) : (
                <p className="fmtm-text-red-medium fmtm-flex fmtm-justify-center fmtm-items-center fmtm-h-full">
                  No Projects Found
                </p>
              )}
            </div>
            <Pagination
              showing={filteredProjectCards?.length}
              totalCount={homeProjectPagination?.total || 0}
              currentPage={homeProjectPagination?.page || 0}
              isLoading={false}
              pageSize={homeProjectPagination.per_page}
              handlePageChange={(page) => setPaginationPage(page)}
              className="fmtm-fixed fmtm-left-0 fmtm-w-full"
            />
            {showMapStatus && <ProjectListMap />}
          </div>
        ) : (
          <div
            className={`fmtm-grid fmtm-gap-3 fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-4 xl:fmtm-grid-cols-5 2xl:fmtm-grid-cols-6 lg:scrollbar fmtm-mt-2`}
          >
            <ProjectCardSkeleton />
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
