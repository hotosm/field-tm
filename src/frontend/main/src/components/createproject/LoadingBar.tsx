import React, { useEffect, useRef } from 'react';
import { Box, Tooltip } from '@mui/material';
import { LinearProgress } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import CoreModules from '../../shared/CoreModules';

const LoadingBar = ({ steps, activeStep, totalSteps }) => {
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

  const calculateRemainingTime = (totalSteps, activeStep, elapsedSeconds) => {
    const averageSecondsPerStep = elapsedSeconds / activeStep;
    const remainingSteps = totalSteps - activeStep;
    const remainingTime = remainingSteps * averageSecondsPerStep;
    return remainingTime.toFixed(2);
  };

  const startTimestamp = useRef(Date.now());

  useEffect(() => {
    startTimestamp.current = Date.now();
  }, [activeStep]);

  const elapsedSeconds = (Date.now() - startTimestamp.current) / 1000;
  const completedPercentage = calculateProgress(steps, activeStep);
  const remainingTime = calculateRemainingTime(steps, activeStep, elapsedSeconds);

  return (
    <Box>
      <Box sx={{ display: 'flex', width: '73%', justifyContent: 'space-between', alignItems: 'center' }}>
        <CoreModules.Typography variant="subtitle6">
          Your Progress
          <CoreModules.Typography variant="subtitle1">{`${completedPercentage}% Completed`}</CoreModules.Typography>
        </CoreModules.Typography>

        <CoreModules.Typography variant="subtitle6">{`${remainingTime} secs remaining`}</CoreModules.Typography>
      </Box>
      <CoreModules.ThemeProvider theme={theme}>
        <Tooltip title={`Step: ${totalSteps} / ${activeStep + 1}`} placement="top">
          <Box
            component="span"
            sx={{
              position: 'absolute',
              borderRadius: '20%',
            }}
          >
            <LinearProgress
              variant="determinate"
              value={completedPercentage}
              sx={{
                borderRadius: '12px',
                height: '20px',
                width: 430,
                backgroundImage: `linear-gradient(to right, ${theme.palette.primary.main} 0%, ${
                  theme.palette.secondary.main
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
