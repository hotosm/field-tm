import * as React from 'react';
import { TransitionProps } from '@mui/material/transitions';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';

const Transition = React.forwardRef(function Transition(
    props: TransitionProps & {
        children: React.ReactElement<any, any>;
    },
    ref: React.Ref<unknown>,
) {
    return <CoreModules.Slide direction="up" ref={ref} {...props} />;
});

export default function BasicDialog({ open, onClose, title, iconCloseMode, actionsButton, element }) {

    return (
        <CoreModules.Stack>
            <CoreModules.Dialog
                fullWidth
                open={open}
                TransitionComponent={Transition}
                keepMounted
                onClose={onClose}
                aria-describedby="alert-dialog-slide-description"
            >
                <CoreModules.Box>
                    {
                        iconCloseMode &&
                        <CoreModules.Stack
                            style={{ float: 'right' }}
                            mt={'2%'}
                            mr={'1%'}
                            borderRadius={60}
                            height={50}
                            width={40}

                        >
                            <CoreModules.IconButton onClick={onClose}>
                                <AssetModules.CloseIcon color='info' />
                            </CoreModules.IconButton>
                        </CoreModules.Stack>
                    }
                    <CoreModules.DialogTitle variant='h2'>{title}</CoreModules.DialogTitle>
                </CoreModules.Box>
                <CoreModules.DialogContent>
                    {element}
                </CoreModules.DialogContent>
                <CoreModules.DialogActions>
                    {
                        iconCloseMode != true && actionsButton
                    }
                </CoreModules.DialogActions>
            </CoreModules.Dialog>
        </CoreModules.Stack>
    );
}