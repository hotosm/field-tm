import * as React from 'react';
import { MenuProps } from '@mui/material/Menu';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';

const StyledMenu = AssetModules.styled((props: MenuProps) => (
    <CoreModules.Menu
        elevation={0}
        anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
        }}
        transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
        }}
        {...props}
    />
))(({ theme }) => ({
    '& .MuiPaper-root': {
        borderRadius: 6,
        marginTop: theme.spacing(1),
        minWidth: 180,
        boxShadow:
            `rgb(255, 255, 255) 0px 0px 0px 0px,
             rgba(0, 0, 0, 0.05) 0px 0px 0px 1px,
             rgba(0, 0, 0, 0.1) 0px 10px 15px -3px,
             rgba(0, 0, 0, 0.05) 0px 4px 6px -2px`,
        '& .MuiMenu-list': {
            padding: '4px 0',
        },

    },
}));

export default function CustomizedMenus({ element, btnProps, btnName }) {
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    return (
        <div>
            <CoreModules.Button
                id="demo-customized-button"
                aria-controls={open ? 'demo-customized-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={open ? 'true' : undefined}
                variant="contained"
                translate='no'
                disableElevation
                onClick={handleClick}
                {...btnProps}
                endIcon={<AssetModules.KeyboardArrowDownIcon />}
            >
                {btnName}
            </CoreModules.Button>
            <StyledMenu
                id="demo-customized-menu"
                MenuListProps={{
                    'aria-labelledby': 'demo-customized-button',
                }}
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
            >
                {element}
            </StyledMenu>
        </div>
    );
}