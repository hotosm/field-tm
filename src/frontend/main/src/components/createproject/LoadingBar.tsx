import React, { useEffect, useRef } from 'react';
import { Box, Tooltip } from '@mui/material';
import { LinearProgress } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import CoreModules from '../../shared/CoreModules';

const LoadingBar = ({ steps, activeStep, totalSteps, title }) => {
  const theme = createTheme({
    palette: {
      primary: {
        main: '#7679d1',
      },
      secondary: {
        main: '#dba7f0',
      },
    },
  });
  const calculateProgress = (totalSteps, activeStep) => {
    return (activeStep / totalSteps) * 100;
  };



  const completedPercentage = calculateProgress(steps, activeStep);

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center' }}>
        <CoreModules.Typography variant="subtitle6" sx={{ width: '100%' }}>
          {title}
          <CoreModules.Typography variant="subtitle1">{`${completedPercentage.toFixed(2)}% Completed`}</CoreModules.Typography>
          <CoreModules.Typography sx={{ display: 'flex', width: '100%', justifyContent: 'flex-end' }} variant="subtitle2">{`${activeStep} out of ${totalSteps} Tasks`}</CoreModules.Typography>
        </CoreModules.Typography>
      </Box>
      <CoreModules.ThemeProvider theme={theme}>
        <Tooltip title={`Step: ${totalSteps} / ${activeStep + 1}`} placement="top">
          <Box
            component="span"
            sx={{
              // position: 'absolute',
              borderRadius: '20%',
            }}
          >
            <LinearProgress
              variant="determinate"
              value={completedPercentage}
              sx={{
                borderRadius: '12px',
                height: '20px',
                width: '100%',
                backgroundImage: `linear-gradient(to right, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main
                  } ${calculateProgress(steps, totalSteps)}%, lightgray ${calculateProgress(
                    steps,
                    activeStep,
                  )}%, lightgray 100%)`,
              }}
            />
          </Box>
        </Tooltip>
      </CoreModules.ThemeProvider>
    </Box>
  );
};

export default LoadingBar;
