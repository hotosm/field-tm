import React from 'react';
import { Link } from 'react-router-dom';
import AssetModules from '@/shared/AssetModules';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { HomeActions } from '@/store/slices/HomeSlice';
import Switch from '@/components/common/Switch';
import Searchbar from '@/components/common/SearchBar';
import Button from '@/components/common/Button';
import { useHasManagedAnyOrganization } from '@/hooks/usePermissions';

type homePageFiltersPropType = {
  searchText: string;
  onSearch: (data: string) => void;
};

const HomePageFilters = ({ searchText, onSearch }: homePageFiltersPropType) => {
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();
  const dispatch = useAppDispatch();

  const showMapStatus = useAppSelector((state) => state.home.showMapStatus);

  return (
    <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-flex-wrap fmtm-gap-2">
      <h5>PROJECTS</h5>
      <Searchbar
        value={searchText}
        onChange={onSearch}
        wrapperStyle="!fmtm-w-[10.313rem] !fmtm-h-9"
        className="!fmtm-rounded !fmtm-h-9"
      />
      <div className="fmtm-flex fmtm-items-center fmtm-justify-end fmtm-gap-3 fmtm-ml-auto sm:fmtm-ml-0">
        <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
          <p className="fmtm-button">Show Map</p>
          <Switch
            ref={null}
            className=""
            checked={showMapStatus}
            onCheckedChange={() => dispatch(HomeActions.SetShowMapStatus(!showMapStatus))}
          />
        </div>
        {hasManagedAnyOrganization && (
          <Link to={'/create-project?step=1'}>
            <Button variant="primary-red">
              <AssetModules.AddIcon className="!fmtm-text-[1.125rem]" />
              <p>New Project</p>
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
};

export default HomePageFilters;
