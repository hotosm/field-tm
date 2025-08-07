import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useGetProjectSummaries } from '@/api/project';
import Searchbar from '@/components/common/SearchBar';
import useDebouncedInput from '@/hooks/useDebouncedInput';
import Switch from '@/components/common/Switch';
import ExploreProjectCard from '@/components/home/ExploreProjectCard';
import Pagination from '@/components/common/Pagination';
import ProjectSummaryMap from '@/components/OrganizationDashboard/ProjectSummaryMap';
import ProjectCardSkeleton from '@/components/Skeletons/Project/ProjectCardSkeleton';
import { project_status } from '@/types/enums';

type filterType = {
  page: number;
  results_per_page: number;
  search: string;
  status: project_status | undefined;
  org_id: number;
};

const initialData = {
  results: [],
  pagination: {
    has_next: false,
    has_prev: false,
    next_num: null,
    page: null,
    pages: null,
    prev_num: null,
    per_page: 12,
    total: null,
  },
};

const ProjectSummary = () => {
  const params = useParams();
  const organizationId = params.id;

  const [showMap, setShowMap] = useState(true);
  const [filter, setFilter] = useState<filterType>({
    page: 1,
    results_per_page: 12,
    search: '',
    status: undefined,
    org_id: +organizationId!,
  });
  const [searchTextData, handleChangeData] = useDebouncedInput({
    ms: 400,
    init: filter.search,
    onChange: (e) => {
      setFilter({ ...filter, search: e.target.value, page: 1 });
    },
  });

  const { data: projectSummaryData, isLoading: isProjectListLoading } = useGetProjectSummaries({
    params: filter,
    queryOptions: { queryKey: ['project-summaries', filter] },
  });
  const { results: projectList, pagination } = projectSummaryData || initialData;

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
              {isProjectListLoading ? (
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
            totalCount={pagination?.total || 0}
            currentPage={pagination?.page || 0}
            isLoading={false}
            pageSize={pagination.per_page}
            handlePageChange={(page) => setFilter({ ...filter, page: page })}
            className="fmtm-relative fmtm-border-b fmtm-border-x fmtm-border-[#E2E2E2] fmtm-rounded-b-lg"
          />
        </div>
        {showMap && (
          <div className="fmtm-h-[30vh] md:fmtm-h-full">
            <ProjectSummaryMap projectList={projectList} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectSummary;
