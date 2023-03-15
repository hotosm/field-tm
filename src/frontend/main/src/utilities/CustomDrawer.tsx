import * as React from 'react';
import { Drawer } from 'rsuite';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';

const CustomDrawer = ({ open, placement, size, onClose }) => {
  const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)
  const onMouseEnter = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element != null ? element.style.color = `${defaultTheme.palette.error['main']}` : null
  }

  const onMouseLeave = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element != null ? element.style.color = `${defaultTheme.palette.info['main']}` : null

  }

  const Drawerstyles = {
    list: {
      width: '100%',
      bgcolor: 'background.paper',
    },
    outlineBtn: {
      padding: 8,
      width: '100%',
      marginTop: '4%',
      borderRadius: 7,
      fontFamily: defaultTheme.typography.subtitle2.fontFamily
    },
    containedBtn: {
      padding: 8,
      width: '100%',
      marginTop: '0.7%',
      borderRadius: 7,
      fontFamily: defaultTheme.typography.subtitle2.fontFamily
    }
  };

  return (
    <>
      <Drawer
        style={size == 'full' ? { width: '100%' } : { opacity: 1 }}
        size={size}
        placement={placement}
        open={open}
        onClose={onClose}

      >

        <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', padding: 3 }}>
          <CoreModules.Stack sx={{ width: 50, borderRadius: '50%', marginLeft: '0.7%' }}>
            <CoreModules.IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={onClose}
              color="info"
            >
              <AssetModules.CloseIcon />
            </CoreModules.IconButton>
          </CoreModules.Stack>

          <CoreModules.Divider />
          <CoreModules.List sx={Drawerstyles.list} component="nav" aria-label="mailStack folders">
            {
              ['Explore Projects', 'My Contributions', 'Learn', 'About', 'Support'].map((value, index) => {
                return (
                  <CoreModules.ListItem
                    id={index.toString()}
                    onMouseEnter={onMouseEnter}
                    onMouseLeave={onMouseLeave}
                    key={index}
                  >
                    <CoreModules.ListItemText
                      id={`text${index}`}
                      primary={value}

                    />
                  </CoreModules.ListItem>
                )
              })
            }
          </CoreModules.List>
          <CoreModules.Button
            variant="contained"
            color="error"
            startIcon={<AssetModules.LoginIcon />}
            style={Drawerstyles.containedBtn}
            href="/login"
          >
            Sign in
          </CoreModules.Button>
          <CoreModules.Button
            variant="outlined"
            color="error"
            startIcon={<AssetModules.PersonIcon />}
            style={Drawerstyles.outlineBtn}
            href="/signup"
          >
            Sign up
          </CoreModules.Button>

        </CoreModules.Stack>
      </Drawer>
    </>
  );
};

export default CustomDrawer;
