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

interface OrganisationSectionProps {
  isLoading: boolean;
  orgList: any[] | null | undefined;
  searchKeyword: string;
}

const filteredBySearch = (data: GetOrganisationDataModel[], searchKeyword: string) => {
  const filteredCardData: GetOrganisationDataModel[] = data?.filter((d) =>
    d.name.toLowerCase().includes(searchKeyword.toLowerCase()),
  );
  return filteredCardData;
};

const OrganisationListSection = ({ isLoading, orgList, searchKeyword }: OrganisationSectionProps) => {
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

const Organisation = () => {
  useDocumentTitle('Organizations');
  const isAdmin = useIsAdmin();
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();

  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [activeTab, setActiveTab] = useState<0 | 1>(0);
  const [verifiedTab, setVerifiedTab] = useState<boolean>(true);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

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
    <CoreModules.Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        background: '#f5f5f5',
        flex: 1,
        gap: 2,
      }}
    >
      <div className="md:fmtm-hidden fmtm-border-b-white fmtm-border-b-[1px]">
        <div className="fmtm-flex fmtm-justify-between fmtm-items-center">
          <h1 className="fmtm-text-xl sm:fmtm-text-2xl fmtm-mb-1 sm:fmtm-mb-2">MANAGE ORGANIZATIONS</h1>
        </div>
      </div>
      <div className="fmtm-flex fmtm-flex-col md:fmtm-flex-row md:fmtm-justify-between md:fmtm-items-center fmtm-gap-2">
        <CoreModules.Box>
          <CoreModules.Tabs sx={{ minHeight: 'fit-content' }}>
            <CoreModules.Tab
              label="All"
              sx={{
                background: activeTab === 0 ? 'grey' : 'white',
                color: activeTab === 0 ? 'white' : 'grey',
                minWidth: 'fit-content',
                width: 'auto',
                '&:hover': { backgroundColor: '#999797', color: 'white' },
                fontSize: ['14px', '16px', '16px'],
                minHeight: ['26px', '36px', '36px'],
                height: ['30px', '36px', '36px'],
                px: ['12px', '16px', '16px'],
              }}
              className="fmtm-duration-150"
              onClick={() => setActiveTab(0)}
            />
            <CoreModules.Tab
              label="My Organizations"
              sx={{
                background: activeTab === 1 ? 'grey' : 'white',
                color: activeTab === 1 ? 'white' : 'grey',
                marginLeft: ['8px', '12px', '12px'],
                minWidth: 'fit-content',
                width: 'auto',
                '&:hover': { backgroundColor: '#999797', color: 'white' },
                fontSize: ['14px', '16px', '16px'],
                minHeight: ['26px', '36px', '36px'],
                height: ['30px', '36px', '36px'],
                px: ['12px', '16px', '16px'],
              }}
              className="fmtm-duration-150"
              onClick={() => setActiveTab(1)}
            />
            {(!hasManagedAnyOrganization || isAdmin) && (
              <CoreModules.Link to={'/organization/new'}>
                <CoreModules.Button
                  variant="outlined"
                  color="error"
                  startIcon={<AssetModules.AddIcon />}
                  sx={{
                    marginLeft: ['8px', '12px', '12px'],
                    minWidth: 'fit-content',
                    width: 'auto',
                    fontWeight: 'bold',
                    minHeight: ['26px', '36px', '36px'],
                    height: ['30px', '36px', '36px'],
                    px: ['12px', '16px', '16px'],
                  }}
                >
                  New
                </CoreModules.Button>
              </CoreModules.Link>
            )}
          </CoreModules.Tabs>
        </CoreModules.Box>
        {authDetails && authDetails['role'] && authDetails['role'] === user_roles.ADMIN && activeTab === 0 && (
          <CoreModules.Box>
            <CoreModules.Tabs sx={{ minHeight: 'fit-content' }}>
              <CoreModules.Tab
                label="To be Verified"
                sx={{
                  background: !verifiedTab ? 'grey' : 'white',
                  color: !verifiedTab ? 'white' : 'grey',
                  minWidth: 'fit-content',
                  width: 'auto',
                  '&:hover': { backgroundColor: '#999797', color: 'white' },
                  fontSize: ['14px', '16px', '16px'],
                  minHeight: ['26px', '36px', '36px'],
                  height: ['30px', '36px', '36px'],
                  px: ['12px', '16px', '16px'],
                }}
                className="fmtm-duration-150"
                onClick={() => setVerifiedTab(false)}
              />
              <CoreModules.Tab
                label="Verified"
                sx={{
                  background: verifiedTab ? 'grey' : 'white',
                  color: verifiedTab ? 'white' : 'grey',
                  marginLeft: ['8px', '12px', '12px'],
                  minWidth: 'fit-content',
                  width: 'auto',
                  '&:hover': { backgroundColor: '#999797', color: 'white' },
                  fontSize: ['14px', '16px', '16px'],
                  minHeight: ['26px', '36px', '36px'],
                  height: ['30px', '36px', '36px'],
                  px: ['12px', '16px', '16px'],
                }}
                className="fmtm-duration-150"
                onClick={() => setVerifiedTab(true)}
              />
            </CoreModules.Tabs>
          </CoreModules.Box>
        )}
      </div>
      <CoreModules.Box>
        <CoreModules.TextField
          id="search-organization"
          variant="outlined"
          size="small"
          placeholder="Search organization"
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          InputProps={{
            startAdornment: (
              <CoreModules.InputAdornment position="start">
                <AssetModules.SearchIcon />
              </CoreModules.InputAdornment>
            ),
          }}
          className="fmtm-min-w-[14rem] lg:fmtm-w-[20%]"
        />
      </CoreModules.Box>

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
    </CoreModules.Box>
  );
};

export default Organisation;
