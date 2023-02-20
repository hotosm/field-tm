import * as React from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Slide from '@mui/material/Slide';
import { TransitionProps } from '@mui/material/transitions';
import { Box, IconButton, Stack } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
const Transition = React.forwardRef(function Transition(
    props: TransitionProps & {
        children: React.ReactElement<any, any>;
    },
    ref: React.Ref<unknown>,
) {
    return <Slide direction="up" ref={ref} {...props} />;
});

export default function BasicDialog({ open, onClose, title, iconCloseMode, actionsButton, element }) {

    return (
        <Stack>
            <Dialog
                fullWidth
                open={open}
                TransitionComponent={Transition}
                keepMounted
                onClose={onClose}
                aria-describedby="alert-dialog-slide-description"
            >
                <Box>
                    {
                        iconCloseMode &&
                        <Stack
                            style={{ float: 'right' }}
                            mt={'2%'}
                            mr={'1%'}
                            borderRadius={60}
                            height={50}
                            width={40}

                        >
                            <IconButton onClick={onClose}>
                                <CloseIcon color='info' />
                            </IconButton>
                        </Stack>
                    }
                    <DialogTitle variant='h2'>{title}</DialogTitle>
                </Box>
                <DialogContent>
                    {element}
                </DialogContent>
                <DialogActions>
                    {
                        iconCloseMode != true && actionsButton
                    }
                </DialogActions>
            </Dialog>
        </Stack>
    );
}