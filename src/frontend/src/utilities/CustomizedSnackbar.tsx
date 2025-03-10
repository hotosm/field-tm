import * as React from 'react';
import CoreModules from '@/shared/CoreModules';

type customizedSnackbarPropType = {
  duration: number;
  open: boolean;
  message: string;
  variant: string;
  handleClose: () => void;
};

function Alert(props: Record<string, any>, ref: any) {
  return <CoreModules.MuiAlert ref={ref} elevation={6} variant="filled" {...props} />;
}

function SlideTransition(props: Record<string, any>) {
  return <CoreModules.Slide {...props} direction="up" />;
}

export default function CustomizedSnackbars({
  open,
  message,
  variant,
  handleClose,
  duration,
}: customizedSnackbarPropType) {
  return (
    <CoreModules.Stack spacing={2} sx={{ width: '100%' }}>
      <CoreModules.Snackbar
        open={open}
        autoHideDuration={duration}
        onClose={handleClose}
        TransitionComponent={SlideTransition}
      >
        <Alert onClose={handleClose} severity={variant} sx={{ width: '100%' }}>
          <span className="fmtm-body-lg fmtm-leading-none fmtm-whitespace-pre-line">{message}</span>
        </Alert>
      </CoreModules.Snackbar>
    </CoreModules.Stack>
  );
}
