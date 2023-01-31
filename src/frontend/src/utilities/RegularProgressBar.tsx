import * as React from 'react';
import { styled } from '@mui/material/styles';
import Box from '@mui/material/Box';
import CircularProgress, {
  circularProgressClasses,
  CircularProgressProps,
} from '@mui/material/CircularProgress';
import LinearProgress, { linearProgressClasses } from '@mui/material/LinearProgress';
import enviroment from '../enviroment';

const BorderLinearProgress = styled(LinearProgress)(({ theme }) => ({
  height: 10,
  borderRadius: 5,
  [`&.${linearProgressClasses.colorPrimary}`]: {
    backgroundColor: theme.palette.grey[theme.palette.mode === 'light' ? 200 : 800],
  },
  [`& .${linearProgressClasses.bar}`]: {
    borderRadius: 5,
    backgroundColor: theme.palette.mode === 'light' ? enviroment.sysRedColor : '#308fe8',
  },
}));

// Inspired by the former Facebook spinners.


export default function RegularProgressBar({ style }) {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <BorderLinearProgress style={style} color="inherit" variant="determinate" value={50} />
    </Box>
  );
}