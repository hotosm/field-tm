import React, { useEffect, useState } from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { OrganisationDataService } from '@/api/OrganisationService';
import { user_roles } from '@/types/enums';
import CustomizedImage from '@/utilities/CustomizedImage';
import { GetOrganisationDataModel } from '@/models/organisation/organisationModel';

const Organisation = () => {
  const cardStyle = {
    padding: '20px',
    display: 'flex',
    flexDirection: 'row',
    cursor: 'pointer',
    gap: '20px',
    boxShadow: 'none',
    borderRadius: '0px',
  };

  const url = 'https://fmtm.naxa.com.np/d907cf67fe587072a592.png';

  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [activeTab, setActiveTab] = useState<0 | 1>(0);
  const [verifiedTab, setVerifiedTab] = useState<boolean>(false);
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);

  const handleSearchChange = (event) => {
    setSearchKeyword(event.target.value);
  };

  const dispatch = CoreModules.useAppDispatch();

  const oraganizationData: GetOrganisationDataModel[] = CoreModules.useAppSelector(
    (state) => state.organisation.oraganizationData,
  );
  const filteredCardData: GetOrganisationDataModel[] = oraganizationData?.filter((data) =>
    data.name.toLowerCase().includes(searchKeyword.toLowerCase()),
  );

  useEffect(() => {
    dispatch(OrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/`));
  }, []);

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
      <div>
        <p className="fmtm-text-[#9B9999]">
          Showing {filteredCardData?.length} of {oraganizationData?.length} organizations
        </p>
      </div>
      <CoreModules.Box className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 lg:fmtm-grid-cols-3 fmtm-gap-5">
        {filteredCardData?.map((data, index) => (
          <CoreModules.Card key={index} sx={cardStyle}>
            {data.logo ? (
              <div className="fmtm-min-w-[60px] md:fmtm-min-w-[80px] lg:fmtm-min-w-[120px]">
                <CoreModules.CardMedia component="img" src={data.logo} sx={{ width: ['60px', '80px', '120px'] }} />
              </div>
            ) : (
              <div className="fmtm-min-w-[60px] fmtm-max-w-[60px] md:fmtm-min-w-[80px] md:fmtm-max-w-[80px] lg:fmtm-min-w-[120px] lg:fmtm-max-w-[120px]">
                <CustomizedImage status={'card'} style={{ width: '100%' }} />
              </div>
            )}

            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }} className="fmtm-overflow-hidden">
              <h2
                className="fmtm-line-clamp-1 fmtm-text-base sm:fmtm-text-lg fmtm-font-bold fmtm-capitalize"
                title={data.name}
              >
                {data.name}
              </h2>
              <p
                className="fmtm-line-clamp-3 fmtm-text-[#7A7676] fmtm-font-archivo fmtm-text-sm sm:fmtm-text-base"
                title={data.description}
              >
                {data.description}
              </p>
            </CoreModules.Box>
          </CoreModules.Card>
        ))}
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default Organisation;
