import { Box } from '@mui/material';
import React from 'react';
import CoreModules from '../shared/CoreModules';

const CustomizedProgressBar = ({ height, data }) => {
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  return (
    <CoreModules.Stack
      direction={'row'}
      mt={'2%'}
      height={height}
      spacing={0}
      sx={{ borderRadius: 20, backgroundColor: defaultTheme.palette.info['info_rgb'] }}
    >
      <CoreModules.Box
        sx={{
        
          width: `${100 / (data.total_tasks / data.tasks_mapped)}%`,
          backgroundColor: defaultTheme.palette.info['main'],
        }}
      >
        <div>&nbsp;</div>
      </CoreModules.Box>
      <CoreModules.Box
        style={{
          width: `${100 / (data.total_tasks / data.tasks_validated)}%`,
         
          backgroundColor: defaultTheme.palette.success['main'],
        }}
      >
        <div>&nbsp;</div>
      </CoreModules.Box>
      <CoreModules.Box
        sx={{
          width: `${100 / (data.total_tasks / data.tasks_bad)}%`,
          backgroundColor: defaultTheme.palette.error['main'],
         
        }}
      >
        <div>&nbsp;</div>
      </CoreModules.Box>
    </CoreModules.Stack>
  );
};

export default CustomizedProgressBar;
