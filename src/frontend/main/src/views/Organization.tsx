import React, { useState } from 'react';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import SearchIcon from '@mui/icons-material/Search';

const Organization = () => {
  const url = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSI8DK8HCuvWNyHHg8enmbmmf1ue4AeeF3GDw&usqp=CAU';

  const cardStyle = {
    width: 500,
    p: 3,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    cursor: 'pointer',
  };

  const cardData = Array.from({ length: 9 }).map((_, index) => ({
    title: `Organization ${index + 1}`,
    content: 'ADMINISTRATORS',
  }));

  const [searchKeyword, setSearchKeyword] = useState('');

  const handleSearchChange = (event) => {
    setSearchKeyword(event.target.value);
  };

  const filteredCardData = cardData.filter((data) => data.title.toLowerCase().includes(searchKeyword.toLowerCase()));

  return (
    <CoreModules.Box
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'start', background: '#f0efef', flex: 1 }}
    >
      <CoreModules.Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          paddingTop: '2%',
          gap: 2,
          justifyContent: 'flex-start',
          marginLeft: '7.5%',
        }}
      >
        <CoreModules.Typography variant="condensed">MANAGE ORGANIZATIONS</CoreModules.Typography>
        <CoreModules.Button
          variant="outlined"
          color="error"
          startIcon={<AssetModules.AddIcon />}
          sx={{ minWidth: 'fit-content', width: 'auto', fontWeight: 'bold' }}
        >
          New
        </CoreModules.Button>
      </CoreModules.Box>
      <CoreModules.Box sx={{ display: 'flex', justifyContent: 'center', marginLeft: '7.5%', paddingTop: '2%' }}>
        <CoreModules.TextField
          variant="outlined"
          size="small"
          placeholder="Search organization"
          value={searchKeyword}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <CoreModules.InputAdornment position="start">
                <SearchIcon />
              </CoreModules.InputAdornment>
            ),
          }}
        />
      </CoreModules.Box>
      <CoreModules.Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '4rem', justifyContent: 'center', padding: '2%' }}>
        {filteredCardData.map((data, index) => (
          <CoreModules.Card key={index} sx={cardStyle}>
            <CoreModules.Typography variant="subtitle1">{data.title}</CoreModules.Typography>
            <CoreModules.CardContent>
              <CoreModules.Typography variant="subtitle1">{data.content}</CoreModules.Typography>
            </CoreModules.CardContent>
            <CoreModules.Avatar alt="organization" src={url || ''}>
              Org
            </CoreModules.Avatar>
          </CoreModules.Card>
        ))}
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default Organization;
