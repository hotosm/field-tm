import * as React from 'react';
import { Typography } from '@mui/material'
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import Snackbar from '@mui/material/Snackbar';
import MuiAlert from '@mui/material/Alert';
import Slide from '@mui/material/Slide';
const Alert = React.forwardRef(function Alert(props, ref) {
    return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

function SlideTransition(props) {
    return <Slide {...props} direction="up" />;
}

export default function CustomizedSnackbars({ open, message, variant, handleClose, duration }) {

    // const handleClose = (event, reason) => {
    //     if (reason === 'clickaway') {
    //         return;
    //     }
    //     setOpen(false);
    // };

    return (
        <Stack spacing={2} sx={{ width: '100%' }}>
            <Snackbar open={open} autoHideDuration={duration} onClose={handleClose} TransitionComponent={SlideTransition}>
                <Alert onClose={handleClose} severity={variant} sx={{ width: '100%' }}>
                    <Typography
                        variant='h2'
                    >
                        {message}
                    </Typography>
                </Alert>
            </Snackbar>
        </Stack>
    );
}