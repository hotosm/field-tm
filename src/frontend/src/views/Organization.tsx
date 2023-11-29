import React, { useEffect, useState } from 'react';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import environment from '../environment';
import { OrganizationDataService } from '../api/OrganizationService';

const Organization = () => {
  const cardStyle = {
    padding: 2,
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    cursor: 'pointer',
    gap: 5,
  };

  const url = 'https://fmtm.naxa.com.np/d907cf67fe587072a592.png';

  const [searchKeyword, setSearchKeyword] = useState('');
  const [activeTab, setActiveTab] = useState(0);

  const handleSearchChange = (event) => {
    setSearchKeyword(event.target.value);
  };

  const dispatch = CoreModules.useAppDispatch();

  const oraganizationData: any = CoreModules.useAppSelector((state) => state.organization.oraganizationData);
  console.log(oraganizationData, 'oraganizationData');
  const filteredCardData = oraganizationData?.filter((data) =>
    data.name.toLowerCase().includes(searchKeyword.toLowerCase()),
  );

  useEffect(() => {
    dispatch(OrganizationDataService(`${import.meta.env.VITE_API_URL}/organization/`));
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
      className="fmtm-px-[4.5%]"
    >
      <CoreModules.Box className="fmtm-flex fmtm-flex-col sm:fmtm-flex-row sm:fmtm-items-center fmtm-pt-5 fmtm-gap-2 sm:fmtm-gap-4">
        <h1 className="fmtm-text-[1.5rem] lg:fmtm-text-[2.25rem] fmtm-font-bold">MANAGE ORGANIZATIONS</h1>
        <CoreModules.Link to={'/createOrganization'}>
          <CoreModules.Button
            variant="outlined"
            color="error"
            startIcon={<AssetModules.AddIcon />}
            sx={{ minWidth: 'fit-content', width: 'auto', fontWeight: 'bold' }}
          >
            New
          </CoreModules.Button>
        </CoreModules.Link>
      </CoreModules.Box>
      <CoreModules.Box>
        <CoreModules.Tabs>
          <CoreModules.Tab
            label="All"
            sx={{
              background: activeTab === 0 ? 'grey' : 'white',
              color: activeTab === 0 ? 'white' : 'grey',
              minWidth: 'fit-content',
              width: 'auto',
              '&:hover': { backgroundColor: '#fff', color: 'grey' },
              fontSize: '16px',
              minHeight: '36px',
              height: '36px',
            }}
            onClick={() => setActiveTab(0)}
          />
          <CoreModules.Tab
            label="My Organizations"
            sx={{
              background: activeTab === 1 ? 'grey' : 'white',
              color: activeTab === 1 ? 'white' : 'grey',
              marginLeft: '20px',
              minWidth: 'fit-content',
              width: 'auto',
              '&:hover': { backgroundColor: '#fff', color: 'grey' },
              fontSize: '16px',
              minHeight: '36px',
              height: '36px',
            }}
            onClick={() => setActiveTab(1)}
          />
        </CoreModules.Tabs>
      </CoreModules.Box>
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
      <CoreModules.Box className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 fmtm-gap-5">
        {filteredCardData?.map((data, index) => (
          <CoreModules.Card key={index} sx={cardStyle}>
            <CoreModules.CardMedia
              component="img"
              src={data.logo ? data.logo : 'http://localhost:7051/d907cf67fe587072a592.png'}
              sx={{ width: '150px' }}
            />
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <CoreModules.Typography
                variant="subtitle1"
                sx={{ textTransform: 'uppercase' }}
                className="fmtm-line-clamp-1"
                title={data.name}
              >
                {data.name}
              </CoreModules.Typography>
              <CoreModules.Typography
                variant="subtitle3"
                title={data.description}
                className="fmtm-max-h-[4.5em] fmtm-line-clamp-2"
              >
                {data.description}
              </CoreModules.Typography>
              <CoreModules.Link to={data.url} target="_blank" style={{ textDecoration: 'none' }}>
                <CoreModules.Avatar alt={data.title} src={data.logo} sx={{ height: '25px', width: '25px' }}>
                  {!data.logo || data.logo === 'string' ? data.name[0] : url}
                </CoreModules.Avatar>
              </CoreModules.Link>
            </CoreModules.Box>
          </CoreModules.Card>
        ))}
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default Organization;
