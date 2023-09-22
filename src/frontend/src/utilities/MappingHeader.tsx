import React from 'react';
import CoreModules from '../shared/CoreModules';
import environment from '../environment';

const MappingHeader = () => {
  const onToggleOutline = (e) => {
    var styleSheet = document.styleSheets[0];

    if (e.target.checked) {
      styleSheet.insertRule('* {  outline: 1px solid #ff9c84; }', 0);
    } else {
      if (styleSheet && styleSheet.cssRules.length > 0) {
        styleSheet.deleteRule(0);
      }
    }
  };

  return (
    <CoreModules.Box sx={{ display: 'flex', justifyContent: 'space-between', padding: '1rem', fontSize: '14px' }}>
      {environment.nodeEnv === 'development' ? (
        <div>
          <input type="checkbox" onChange={onToggleOutline}></input>
          <p>Toggle Outline</p>
        </div>
      ) : null}
      <CoreModules.Typography color="error" sx={{ fontSize: '14px' }}>
        Mapping our world together
      </CoreModules.Typography>
      <CoreModules.Link
        to="https://www.hotosm.org/"
        style={{ textDecoration: 'none', color: '#d73f3e' }}
        target="_blank"
      >
        hotosm.org
      </CoreModules.Link>
    </CoreModules.Box>
  );
};

export default MappingHeader;
