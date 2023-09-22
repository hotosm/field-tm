import React from 'react';
import pageNoFound from '../assets/images/notFound.png';
import CoreModules from '../shared/CoreModules';
const NotFoundPage = () => {
  return (
    <CoreModules.Stack
      className="notFound"
      backgroundColor="white"
      display="flex"
      flexDirection="column"
      alignItems="center"
      p={3}
    >
      <CoreModules.Typography mt={'9%'} style={{ wordWrap: 'break-word' }} variant="subtitle2">
        The page you were looking for doesn't exist.
      </CoreModules.Typography>
      <CoreModules.Typography style={{ wordWrap: 'break-word' }} variant="h3">
        You may have mistyped the address or the page may have moved.
      </CoreModules.Typography>
      <img src={pageNoFound} style={{ widh: '25%', height: '22%' }} />
    </CoreModules.Stack>
  );
};

export default NotFoundPage;
