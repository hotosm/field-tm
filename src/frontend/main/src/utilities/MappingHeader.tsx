import React from 'react';
import CoreModules from '../shared/CoreModules';

const MappingHeader = () => {
  return (
    <CoreModules.Box sx={{ display: 'flex', justifyContent: 'space-between', padding: '1rem', fontSize: '14px' }}>
      <CoreModules.Typography color="error" sx={{ fontSize: '14px' }}>
        Mapping our world together
      </CoreModules.Typography>
      <CoreModules.Link to="https://www.hotosm.org/" style={{ textDecoration: 'none', color: '#d73f3e' }} target="_blank">
        hotosm.org
      </CoreModules.Link>
    </CoreModules.Box>
  );
};

export default MappingHeader;
