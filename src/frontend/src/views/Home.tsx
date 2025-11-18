import React, { useState } from 'react';
import { motion } from 'motion/react';
import useDebouncedInput from '@/hooks/useDebouncedInput';
import { useAppSelector } from '@/types/reduxTypes';
import type { field_mapping_app as field_mapping_app_type, project_status } from '@/types/enums';
import { useGetProjectSummariesQuery } from '@/api/project';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import ExploreProjectCard from '@/components/home/ExploreProjectCard';
import HomePageFilters from '@/components/home/HomePageFilters';
import ProjectListMap from '@/components/home/ProjectListMap';
import Pagination from '@/components/common/Pagination';
import ProjectCardSkeleton from '@/components/Skeletons/Project/ProjectCardSkeleton';

type filterType = {
  page: number;
  results_per_page: number;
  search: string;
  status: project_status | undefined;
  field_mapping_app: field_mapping_app_type | undefined;
  country: string;
  my_projects: boolean;
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

const Home = () => {
  useDocumentTitle('Explore Projects');

  const [filter, setFilter] = useState<filterType>({
    page: 1,
    results_per_page: 12,
    search: '',
    field_mapping_app: undefined,
    status: undefined,
    country: '',
    my_projects: false,
  });

  const [searchTextData, handleChangeData] = useDebouncedInput({
    ms: 400,
    init: filter.search,
    onChange: (e) => {
      setFilter({ ...filter, search: e.target.value, page: 1 });
    },
  });

  const [countrySearch, handleCountrySearchChange] = useDebouncedInput({
    ms: 400,
    init: filter.country,
    onChange: (e) => {
      setFilter({ ...filter, country: e.target.value, page: 1 });
    },
  });

  const showMapStatus = useAppSelector((state) => state.home.showMapStatus);

  const { data: projectSummaryData, isLoading: isProjectListLoading } = useGetProjectSummariesQuery({
    params: filter,
    options: { queryKey: ['project-summaries', filter] },
  });
  const { results: projectList, pagination } = projectSummaryData || initialData;

  return (
    <div
      style={{ flex: 1, background: '#F5F5F5' }}
      className="fmtm-flex fmtm-flex-col fmtm-justify-between fmtm-h-full lg:fmtm-overflow-hidden"
    >
      <div className="fmtm-h-full">
        <HomePageFilters
          filter={{
            searchText: searchTextData,
            onSearch: handleChangeData,
            fieldMappingApp: filter.field_mapping_app,
            onFieldMappingAppChange: (value) => setFilter({ ...filter, field_mapping_app: value, page: 1 }),
            status: filter.status,
            onStatusChange: (value) => setFilter({ ...filter, status: value, page: 1 }),
            country: countrySearch,
            onCountrySearch: handleCountrySearchChange,
            myProjects: filter.my_projects,
            onMyProjectsToggle: (state) => setFilter({ ...filter, my_projects: state, page: 1 }),
          }}
        />
        {!isProjectListLoading ? (
          <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 fmtm-mt-2 md:fmtm-overflow-hidden lg:fmtm-h-[calc(100%-85px)] fmtm-pb-16 lg:fmtm-pb-0">
            <div
              className={`fmtm-w-full fmtm-flex fmtm-flex-col fmtm-justify-between md:fmtm-overflow-y-scroll md:scrollbar ${showMapStatus ? 'lg:fmtm-w-[50%]' : ''} `}
            >
              {projectList.length > 0 ? (
                <>
                  <div
                    className={`fmtm-grid fmtm-gap-3 ${
                      !showMapStatus
                        ? 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-4 xl:fmtm-grid-cols-5 2xl:fmtm-grid-cols-6'
                        : 'fmtm-grid-cols-1 sm:fmtm-grid-cols-2 md:fmtm-grid-cols-3 lg:fmtm-grid-cols-2 2xl:fmtm-grid-cols-3 lg:fmtm-overflow-y-scroll lg:scrollbar'
                    }`}
                  >
                    {projectList.map((value, index) => (
                      <motion.div
                        key={index}
                        initial={{ x: -10, y: 0, opacity: 0 }}
                        whileInView={{ x: 0, y: 0, opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <ExploreProjectCard data={value} key={index} />
                      </motion.div>
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
              showing={projectList?.length}
              totalCount={pagination?.total || 0}
              currentPage={pagination?.page || 0}
              isLoading={false}
              pageSize={pagination.per_page}
              handlePageChange={(page) => setFilter({ ...filter, page: page })}
              className="fmtm-fixed fmtm-left-0 fmtm-w-full"
            />
            {showMapStatus && <ProjectListMap projectList={projectList} />}
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
