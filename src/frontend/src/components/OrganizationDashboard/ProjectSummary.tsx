import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useParams } from 'react-router-dom';
import { HomeSummaryService } from '@/api/HomeService';
import Searchbar from '@/components/common/SearchBar';
import useDebouncedInput from '@/hooks/useDebouncedInput';
import Switch from '@/components/common/Switch';
import ExploreProjectCard from '../home/ExploreProjectCard';
import Pagination from '@/components/common/Pagination';
import ProjectSummaryMap from '@/components/OrganizationDashboard/ProjectSummaryMap';
import ProjectCardSkeleton from '@/components/Skeletons/Project/ProjectCardSkeleton';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const ProjectSummary = () => {
  const dispatch = useAppDispatch();
  const params = useParams();

  const organizationId = params.id;

  const [showMap, setShowMap] = useState(true);
  const [search, setSearch] = useState('');
  const [paginationPage, setPaginationPage] = useState(1);

  const [searchTextData, handleChangeData] = useDebouncedInput({
    ms: 500,
    init: search,
    onChange: (e) => setSearch(e.target.value),
  });

  const projectList = useAppSelector((state) => state.home.homeProjectSummary);
  const projectListLoading = useAppSelector((state) => state.home.homeProjectLoading);
  const projectListPagination = useAppSelector((state) => state.home.homeProjectPagination);

  useEffect(() => {
    dispatch(
      HomeSummaryService(`${VITE_API_URL}/projects/summaries`, {
        page: paginationPage,
        results_per_page: 12,
        search,
        org_id: organizationId ? +organizationId : undefined,
      }),
    );
  }, [search, paginationPage]);

  return (
    <div className="fmtm-bg-white fmtm-rounded-lg fmtm-p-5 fmtm-flex-1 md:fmtm-overflow-hidden">
      <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-flex-wrap fmtm-pb-4">
        <h4 className="fmtm-text-grey-800">Project Location Map</h4>
        <Searchbar value={searchTextData} onChange={handleChangeData} wrapperStyle="!fmtm-w-[10.5rem]" isSmall />
        <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
          <p className="fmtm-body-md fmtm-text-grey-800">Show Map</p>
          <Switch ref={null} className="" checked={showMap} onCheckedChange={() => setShowMap(!showMap)} />
        </div>
      </div>
      <div
        className={`md:fmtm-h-[calc(100%-56px)] fmtm-grid fmtm-gap-5 ${showMap ? 'fmtm-grid-cols-1 md:fmtm-grid-cols-2' : 'fmtm-grid-cols-1'}`}
      >
        <div className="fmtm-h-full md:fmtm-overflow-hidden">
          <div className="md:fmtm-h-[calc(100%-49px)] fmtm-relative md:fmtm-overflow-y-scroll md:scrollbar">
            <div
              className={`fmtm-grid ${showMap ? 'fmtm-grid-cols-2 xl:fmtm-grid-cols-3' : 'fmtm-grid-cols-2 sm:fmtm-grid-cols-3 md:fmtm-grid-cols-4 xl:fmtm-grid-cols-5'} fmtm-gap-2 sm:fmtm-gap-3`}
            >
              {projectListLoading ? (
                <ProjectCardSkeleton className="fmtm-border fmtm-border-[#EDEDED]" />
              ) : projectList?.length === 0 ? (
                <p
                  className={`${showMap ? 'fmtm-col-span-2 xl:fmtm-col-span-3' : 'fmtm-col-span-2 sm:fmtm-col-span-3 md:fmtm-col-span-4 xl:fmtm-col-span-5'} fmtm-mx-auto fmtm-mt-14 fmtm-text-grey-500`}
                >
                  Organization has no projects
                </p>
              ) : (
                projectList?.map((project) => (
                  <ExploreProjectCard key={project.id} data={project} className="fmtm-border fmtm-border-[#EDEDED]" />
                ))
              )}
            </div>
          </div>
          <Pagination
            showing={projectList?.length}
            totalCount={projectListPagination?.total || 0}
            currentPage={projectListPagination?.page || 0}
            isLoading={false}
            pageSize={projectListPagination.per_page}
            handlePageChange={(page) => setPaginationPage(page)}
            className="fmtm-relative fmtm-border-b fmtm-border-x fmtm-border-[#E2E2E2] fmtm-rounded-b-lg"
          />
        </div>
        {showMap && (
          <div className="fmtm-h-[30vh] md:fmtm-h-full">
            <ProjectSummaryMap />
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectSummary;
