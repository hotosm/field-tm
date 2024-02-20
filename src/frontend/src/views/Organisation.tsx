import React, { useEffect, useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { MyOrganisationDataService, OrganisationDataService } from '@/api/OrganisationService';
import { user_roles } from '@/types/enums';
import { GetOrganisationDataModel } from '@/models/organisation/organisationModel';
import OrganisationGridCard from '@/components/organisation/OrganisationGridCard';
import { useNavigate } from 'react-router-dom';

const Organisation = () => {
  const navigate = useNavigate();

  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [activeTab, setActiveTab] = useState<0 | 1>(0);
  const [verifiedTab, setVerifiedTab] = useState<boolean>(true);
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);

  const handleSearchChange = (event) => {
    setSearchKeyword(event.target.value);
  };

  const dispatch = CoreModules.useAppDispatch();

  const organisationData: GetOrganisationDataModel[] = CoreModules.useAppSelector(
    (state) => state.organisation.organisationData,
  );
  const myOrganisationData: GetOrganisationDataModel[] = CoreModules.useAppSelector(
    (state) => state.organisation.myOrganisationData,
  );
  const filteredBySearch = (data, searchKeyword) => {
    const filteredCardData: GetOrganisationDataModel[] = data?.filter((d) =>
      d.name.toLowerCase().includes(searchKeyword.toLowerCase()),
    );
    return filteredCardData;
  };
  useEffect(() => {
    dispatch(MyOrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/my-organisations`));
  }, []);
  useEffect(() => {
    if (verifiedTab) {
      dispatch(OrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/`));
    } else {
      dispatch(OrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/unapproved/`));
    }
  }, [verifiedTab]);

  const approveOrganization = (id: number) => {
    navigate(`/approve-organization/${id}`);
  };

  return (
    <CoreModules.Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        background: '#f0efef',
        flex: 1,
        gap: 2,
      }}
      className="fmtm-p-5"
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
            <CoreModules.Link to={'/create-organization'}>
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
          </CoreModules.Tabs>
        </CoreModules.Box>
        {token !== null && token['role'] && token['role'] === user_roles.ADMIN && (
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
        <OrganisationGridCard
          filteredData={filteredBySearch(organisationData, searchKeyword)}
          allDataLength={organisationData?.length}
        />
      ) : null}
      {activeTab === 1 ? (
        <OrganisationGridCard
          filteredData={filteredBySearch(myOrganisationData, searchKeyword)}
          allDataLength={myOrganisationData?.length}
        />
      ) : null}
    </CoreModules.Box>
  );
};

export default Organisation;
