import React, { useEffect, useState } from 'react';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import environment from '../environment';
import { OrganizationDataService } from '../api/OrganizationService';

const Organization = () => {
  const url = 'http://localhost:8080/d907cf67fe587072a592.png';

  const cardStyle = {
    width: 520,
    padding: 3,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    cursor: 'pointer',
  };

  const [searchKeyword, setSearchKeyword] = useState('');

  const handleSearchChange = (event) => {
    setSearchKeyword(event.target.value);
  };

  const dispatch = CoreModules.useDispatch();

  const oraganizationData: any = CoreModules.useSelector<any>((state) => state.organization.oraganizationData);
  const filteredCardData = oraganizationData?.filter((data) =>
    data.name.toLowerCase().includes(searchKeyword.toLowerCase()),
  );

  useEffect(() => {
    dispatch(OrganizationDataService(`${environment.baseApiUrl}/projects/organization/`));
  }, []);

  return (
    <CoreModules.Box
      sx={{ display: 'flex', flexDirection: 'column', background: '#f0efef', flex: 1, gap: 4, paddingLeft: '6%' }}
    >
      <CoreModules.Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          paddingTop: '2%',
          gap: 2,
        }}
      >
        <CoreModules.Typography variant="condensed">MANAGE ORGANIZATIONS</CoreModules.Typography>
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
      <CoreModules.Box sx={{}}>
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
        />
      </CoreModules.Box>
      <CoreModules.Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '3rem' }}>
        {filteredCardData?.map((data, index) => (
          <CoreModules.Card key={index} sx={cardStyle}>
            <CoreModules.Typography variant="subtitle1">{data.name}</CoreModules.Typography>
            <CoreModules.CardContent>
              <CoreModules.Typography variant="subtitle3">{data.description}</CoreModules.Typography>
            </CoreModules.CardContent>
            <CoreModules.Link to={data.url} target="_blank">
              <CoreModules.Avatar alt={data.title} src={data.logo}>
                {!data.logo || data.logo === 'string' ? data.name[0] : null}
              </CoreModules.Avatar>
            </CoreModules.Link>
          </CoreModules.Card>
        ))}
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default Organization;
