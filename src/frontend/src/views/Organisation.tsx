import React, { useEffect, useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { MyOrganisationDataService, OrganisationDataService } from '@/api/OrganisationService';
import { user_roles } from '@/types/enums';
import { GetOrganisationDataModel } from '@/models/organisation/organisationModel';
import OrganisationGridCard from '@/components/organisation/OrganisationGridCard';
import windowDimention from '@/hooks/WindowDimension';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useHasManagedAnyOrganization, useIsAdmin } from '@/hooks/usePermissions';
import OrganizationCardSkeleton from '@/components/Skeletons/Organization/OrganizationCardSkeleton';

const Organisation = () => {
  useDocumentTitle('Organizations');
  const dispatch = useAppDispatch();
  const { type } = windowDimention();
  const isAdmin = useIsAdmin();
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();

  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [activeTab, setActiveTab] = useState<0 | 1>(0);
  const [verifiedTab, setVerifiedTab] = useState<boolean>(true);
  const [myOrgsLoaded, setMyOrgsLoaded] = useState(false);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  const organisationData = useAppSelector((state) => state.organisation.organisationData);
  const myOrganisationData = useAppSelector((state) => state.organisation.myOrganisationData);

  const organisationDataLoading = useAppSelector((state) => state.organisation.organisationDataLoading);
  const myOrganisationDataLoading = useAppSelector((state) => state.organisation.myOrganisationDataLoading);
  // loading states for the organisations from selector

  let cardsPerRow = new Array(
    type == 'xl' ? 3 : type == 'lg' ? 3 : type == 'md' ? 3 : type == 'sm' ? 2 : type == 's' ? 2 : 1,
  ).fill(0);
  // calculate number of cards to display according to the screen size

  const handleSearchChange = (event) => {
    setSearchKeyword(event.target.value);
  };
  const filteredBySearch = (data: GetOrganisationDataModel[], searchKeyword: string) => {
    const filteredCardData: GetOrganisationDataModel[] = data?.filter((d) =>
      d.name.toLowerCase().includes(searchKeyword.toLowerCase()),
    );
    return filteredCardData;
  };

  useEffect(() => {
    if (verifiedTab) {
      dispatch(OrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation`));
    } else {
      dispatch(OrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/unapproved`));
    }
  }, [verifiedTab]);

  const loadMyOrganisations = () => {
    if (!myOrgsLoaded) {
      dispatch(MyOrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/my-organisations`));
      setMyOrgsLoaded(true);
    }
    setActiveTab(1);
  };

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
              onClick={() => loadMyOrganisations()}
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
          onChange={handleSearchChange}
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
      {activeTab === 0 ? (
        organisationDataLoading ? (
          <div className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 lg:fmtm-grid-cols-3 fmtm-gap-5 fmtm-w-full">
            {Array.from({ length: 12 }).map((_, i) => (
              <OrganizationCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <OrganisationGridCard
            filteredData={filteredBySearch(organisationData, searchKeyword)}
            allDataLength={organisationData?.length}
          />
        )
      ) : null}
      {activeTab === 1 ? (
        organisationDataLoading ? (
          <div className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 lg:fmtm-grid-cols-3 fmtm-gap-5 fmtm-w-full">
            {Array.from({ length: 12 }).map((_, i) => (
              <OrganizationCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <OrganisationGridCard
            filteredData={filteredBySearch(myOrganisationData, searchKeyword)}
            allDataLength={myOrganisationData?.length}
          />
        )
      ) : null}
    </CoreModules.Box>
  );
};

export default Organisation;
