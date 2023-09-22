import * as React from 'react';
import CoreModules from '../shared/CoreModules';
const Alert = React.forwardRef(function Alert(props, ref) {
  return <CoreModules.MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

function SlideTransition(props) {
  return <CoreModules.Slide {...props} direction="up" />;
}

export default function CustomizedSnackbars({ open, message, variant, handleClose, duration }) {
  return (
    <CoreModules.Stack spacing={2} sx={{ width: '100%' }}>
      <CoreModules.Snackbar
        open={open}
        autoHideDuration={duration}
        onClose={handleClose}
        TransitionComponent={SlideTransition}
      >
        <Alert onClose={handleClose} severity={variant} sx={{ width: '100%' }}>
          <CoreModules.Typography variant="h2">{message}</CoreModules.Typography>
        </Alert>
      </CoreModules.Snackbar>
    </CoreModules.Stack>
  );
}
