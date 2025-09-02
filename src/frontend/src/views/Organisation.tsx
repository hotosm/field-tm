import React, { useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { user_roles } from '@/types/enums';
import { GetOrganisationDataModel } from '@/models/organisation/organisationModel';
import OrganisationGridCard from '@/components/organisation/OrganisationGridCard';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useHasManagedAnyOrganization, useIsAdmin } from '@/hooks/usePermissions';
import OrganizationCardSkeleton from '@/components/Skeletons/Organization/OrganizationCardSkeleton';
import {
  useGetMyOrganisationsQuery,
  useGetOrganisationsQuery,
  useGetUnapprovedOrganisationsQuery,
} from '@/api/organisation';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';
import Searchbar from '@/components/common/SearchBar';
import useDebouncedInput from '@/hooks/useDebouncedInput';

type OrganisationSectionPropsType = {
  isLoading: boolean;
  orgList: any[] | null | undefined;
  searchKeyword: string;
};

type TabType = {
  label: string;
  isActive: boolean;
  onClick: () => void;
};

const filteredBySearch = (data: GetOrganisationDataModel[], searchKeyword: string) => {
  const filteredCardData: GetOrganisationDataModel[] = data?.filter((d) =>
    d.name.toLowerCase().includes(searchKeyword.toLowerCase()),
  );
  return filteredCardData;
};

const OrganisationListSection = ({ isLoading, orgList, searchKeyword }: OrganisationSectionPropsType) => {
  if (isLoading) {
    return (
      <div className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 lg:fmtm-grid-cols-3 fmtm-gap-5 fmtm-w-full">
        {Array.from({ length: 12 }).map((_, i) => (
          <OrganizationCardSkeleton key={i} />
        ))}
      </div>
    );
  }
  if (orgList) {
    return (
      <OrganisationGridCard filteredData={filteredBySearch(orgList, searchKeyword)} allDataLength={orgList.length} />
    );
  }
  return null;
};

const Tab = ({ label, isActive, onClick }: TabType) => {
  console.log(isActive);
  return (
    <div
      onClick={onClick}
      className={`fmtm-w-fit hover:fmtm-bg-[#999797] hover:fmtm-text-white fmtm-px-4 fmtm-py-1 fmtm-cursor-pointer fmtm-duration-200 fmtm-font-medium ${isActive ? ' fmtm-bg-[#808080] fmtm-text-white' : 'fmtm-bg-white fmtm-text-[#808080]'}`}
    >
      {label}
    </div>
  );
};

const Organisation = () => {
  useDocumentTitle('Organizations');
  const navigate = useNavigate();
  const isAdmin = useIsAdmin();
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();

  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [activeTab, setActiveTab] = useState<0 | 1>(0);
  const [verifiedTab, setVerifiedTab] = useState<boolean>(true);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

  const [searchTextData, handleChangeData] = useDebouncedInput({
    ms: 400,
    init: '',
    onChange: (e) => {
      setSearchKeyword(e.target.value);
    },
  });

  const { data: organisationList, isLoading: isOrganisationListLoading } = useGetOrganisationsQuery({
    options: { queryKey: ['get-organisation-list'], enabled: activeTab === 0 && verifiedTab },
  });

  const { data: myOrganisationList, isLoading: isMyOrganisationListLoading } = useGetMyOrganisationsQuery({
    options: { queryKey: ['get-my-organisation-list'], enabled: activeTab === 1 },
  });

  const { data: unapprovedOrganisationList, isLoading: isUnapprovedOrganisationListLoading } =
    useGetUnapprovedOrganisationsQuery({
      options: { queryKey: ['get-unapproved-organisation-list'], enabled: activeTab === 0 && !verifiedTab },
    });

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-3">
      {/* tab filters */}
      <div className="fmtm-w-full fmtm-flex fmtm-items-center fmtm-justify-between fmtm-flex-wrap fmtm-gap-y-3">
        <div className="fmtm-flex fmtm-gap-3">
          <Tab label="ALL" isActive={activeTab === 0} onClick={() => setActiveTab(0)} />
          <Tab label="MY ORGANIZATIONS" isActive={activeTab === 1} onClick={() => setActiveTab(1)} />
          {(!hasManagedAnyOrganization || isAdmin) && (
            <Button variant="secondary-red" onClick={() => navigate('/organization/new')} className="!fmtm-py-1">
              <AssetModules.AddIcon />
              NEW
            </Button>
          )}
        </div>
        {authDetails && authDetails['role'] && authDetails['role'] === user_roles.ADMIN && activeTab === 0 && (
          <div className="fmtm-flex fmtm-gap-3">
            <Tab label="TO BE VERIFIED" isActive={!verifiedTab} onClick={() => setVerifiedTab(false)} />
            <Tab label="VERIFIED" isActive={verifiedTab} onClick={() => setVerifiedTab(true)} />
          </div>
        )}
      </div>

      <Searchbar
        value={searchTextData}
        onChange={handleChangeData}
        wrapperStyle="fmtm-min-w-[14rem] fmtm-max-w-[20.6rem]"
        isSmall
      />

      {/* Verified Organisations */}
      {activeTab === 0 && verifiedTab && (
        <OrganisationListSection
          isLoading={isOrganisationListLoading}
          orgList={organisationList}
          searchKeyword={searchKeyword}
        />
      )}

      {/* Unverified Organisations */}
      {activeTab === 0 && !verifiedTab && (
        <OrganisationListSection
          isLoading={isUnapprovedOrganisationListLoading}
          orgList={unapprovedOrganisationList}
          searchKeyword={searchKeyword}
        />
      )}

      {/* My Organisations */}
      {activeTab === 1 && (
        <OrganisationListSection
          isLoading={isMyOrganisationListLoading}
          orgList={myOrganisationList}
          searchKeyword={searchKeyword}
        />
      )}
    </div>
  );
};

export default Organisation;
