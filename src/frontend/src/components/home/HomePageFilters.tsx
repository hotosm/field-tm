import React from 'react';
import { Link } from 'react-router-dom';
import AssetModules from '@/shared/AssetModules';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { HomeActions } from '@/store/slices/HomeSlice';
import Switch from '@/components/common/Switch';
import Searchbar from '@/components/common/SearchBar';
import Button from '@/components/common/Button';
import { useHasManagedAnyOrganization } from '@/hooks/usePermissions';
import Select2 from '@/components/common/Select2';
import { field_mapping_app, project_status } from '@/types/enums';
import Toggle from '@/components/common/Toggle';

type homePageFiltersPropType = {
  searchText: string;
  onSearch: (data: string) => void;
  status: project_status | undefined;
  onStatusChange: (data: project_status) => void;
  fieldMappingApp: field_mapping_app | undefined;
  onFieldMappingAppChange: (data: field_mapping_app) => void;
  country: string;
  onCountrySearch: (data: string) => void;
  myProjects: boolean;
  onMyProjectsToggle: (state: boolean) => void;
};

type statusOptionType = { value: project_status; label: string };
type fieldMappingAppOptionType = { value: field_mapping_app; label: string };

const statusOptions: statusOptionType[] = [
  {
    value: project_status.DRAFT,
    label: 'Draft',
  },
  {
    value: project_status.PUBLISHED,
    label: 'Published',
  },
  {
    value: project_status.COMPLETED,
    label: 'Completed',
  },
];
const fieldMappingAppOptions: fieldMappingAppOptionType[] = [
  {
    value: field_mapping_app.FieldTM,
    label: 'FieldTM',
  },
  {
    value: field_mapping_app.ODK,
    label: 'ODK',
  },
  {
    value: field_mapping_app.QField,
    label: 'QField',
  },
];

const HomePageFilters = ({ filter }: { filter: homePageFiltersPropType }) => {
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();
  const dispatch = useAppDispatch();

  const showMapStatus = useAppSelector((state) => state.home.showMapStatus);

  return (
    <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-flex-wrap fmtm-gap-2">
      <h5>PROJECTS</h5>
      <div className="fmtm-flex fmtm-items-center fmtm-gap-5 fmtm-flex-wrap">
        <Select2
          options={fieldMappingAppOptions}
          value={filter.fieldMappingApp || ''}
          choose="value"
          onChange={(value) => filter.onFieldMappingAppChange(value || undefined)}
          placeholder="Mapping App"
          placeholderClassName="fmtm-text-sm"
          className="!fmtm-w-[10.313rem] fmtm-bg-white !fmtm-rounded focus:fmtm-ring-0"
          enableSearchbar={false}
        />
        <Select2
          options={statusOptions}
          value={filter.status || ''}
          choose="value"
          onChange={(value) => filter.onStatusChange(value || undefined)}
          placeholder="Status"
          placeholderClassName="fmtm-text-sm"
          className="!fmtm-w-[10.313rem] fmtm-bg-white !fmtm-rounded focus:fmtm-ring-0"
          enableSearchbar={false}
        />
        <Searchbar
          value={filter.searchText}
          onChange={filter.onSearch}
          placeholder="Project Name or ID"
          wrapperStyle="!fmtm-w-[11.7rem] !fmtm-h-9"
          className="!fmtm-rounded !fmtm-h-9 placeholder:fmtm-text-sm"
        />
        <Searchbar
          value={filter.country}
          onChange={filter.onCountrySearch}
          placeholder="Country Name or Code"
          wrapperStyle="!fmtm-w-[11.7rem] !fmtm-h-9"
          className="!fmtm-rounded !fmtm-h-9 placeholder:fmtm-text-sm"
        />
        <Toggle
          label="My Projects"
          isToggled={filter.myProjects}
          onToggle={filter.onMyProjectsToggle}
          tooltipMessage={`Toggle to view ${!filter.myProjects ? 'your projects' : 'all projects'}`}
        />
      </div>
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
