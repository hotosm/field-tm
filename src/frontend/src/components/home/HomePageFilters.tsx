import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import Switch from '@/components/common/Switch';
import { HomeActions } from '@/store/slices/HomeSlice';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';

type homePageFiltersPropType = {
  onSearch: (data: string) => void;
  filteredProjectCount: number;
};

//Home Filter
const HomePageFilters = ({ onSearch, filteredProjectCount }: homePageFiltersPropType) => {
  const dispatch = useAppDispatch();

  const showMapStatus = useAppSelector((state) => state.home.showMapStatus);
  const homeProjectPagination = useAppSelector((state) => state.home.homeProjectPagination);

  return (
    <CoreModules.Stack>
      {/* Create New Project Button  */}
      <div>
        <div className="fmtm-flex fmtm-flex-col sm:fmtm-flex-row sm:fmtm-items-center fmtm-gap-4">
          <h5 className="fmtm-text-2xl">PROJECTS</h5>
          <CoreModules.Link
            to={'/create-project'}
            style={{
              textDecoration: 'none',
            }}
          >
            <button className="fmtm-bg-primaryRed fmtm-text-sm sm:fmtm-text-[1rem] fmtm-px-4 fmtm-py-2 fmtm-rounded fmtm-w-auto fmtm-text-white fmtm-uppercase">
              + Create New Project{' '}
            </button>
          </CoreModules.Link>
        </div>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-3 sm:fmtm-flex-row sm:fmtm-justify-between">
          <div className="fmtm-mt-3 fmtm-flex fmtm-items-center fmtm-gap-1">
            <div className=" fmtm-border-[#E7E2E2] fmtm-border-2 sm:fmtm-w-fit fmtm-flex fmtm-bg-white fmtm-p-2 fmtm-items-center">
              <input
                type="search"
                className="fmtm-h-7 fmtm-p-2 fmtm-w-full fmtm-outline-none"
                placeholder="Search Projects"
                onChange={(e) => onSearch(e.target.value)}
              ></input>
              <AssetModules.SearchIcon />
            </div>
          </div>
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <p>Show Map</p>
            <Switch
              ref={null}
              className=""
              checked={showMapStatus}
              onCheckedChange={() => dispatch(HomeActions.SetShowMapStatus(!showMapStatus))}
            />
          </div>
        </div>
        <div className="fmtm-mt-6 fmtm-mb-1 fmtm-flex fmtm-items-center fmtm-justify-between">
          <p className="fmtm-text-[#A8A6A6]">
            Showing {filteredProjectCount} of {homeProjectPagination.total} projects
          </p>
        </div>
      </div>
    </CoreModules.Stack>
  );
};

export default HomePageFilters;
