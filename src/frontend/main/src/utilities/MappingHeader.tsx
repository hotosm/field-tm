import React from 'react';
import CoreModules from '../shared/CoreModules';

const MappingHeader = () => {
  return (
    <CoreModules.Box sx={{ display: 'flex', justifyContent: 'space-between', padding: '1rem' }}>
      <CoreModules.Typography color="error">Mapping our world together</CoreModules.Typography>
      <CoreModules.Link
        to="https://fmtm.naxa.com.np/"
        style={{ textDecoration: 'none', color: '#d73f3e' }}
        target="_blank"
      >
        fmtm.naxa
      </CoreModules.Link>
    </CoreModules.Box>
  );
};

export default MappingHeader;
