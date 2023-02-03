import * as React from 'react';
import { Drawer } from 'rsuite';
import { Box } from '@mui/system';
import { Button, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import PersonIcon from '@mui/icons-material/Person';
import LoginIcon from '@mui/icons-material/Login';
import { useSelector } from 'react-redux';



const CustomDrawer = ({ open, placement, size, onClose }) => {
  const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
  const onMouseEnter = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element != null ? element.style.color = `${defaultTheme.palette.error['main']}` : null
  }

  const onMouseLeave = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element != null ? element.style.color = `${defaultTheme.palette.primary['main']}` : null

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

        <Box sx={{ display: 'flex', flexDirection: 'column', padding: 3 }}>
          <Box sx={{ width: 50, borderRadius: '50%', marginLeft: '0.7%' }}>

            <IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={onClose}
              color="info"
            >
              <CloseIcon />
            </IconButton>
          </Box>

          <Divider />
          <List sx={Drawerstyles.list} component="nav" aria-label="mailbox folders">
            {
              ['Explore Projects', 'My Contributions', 'Learn', 'About', 'Support'].map((value, index) => {
                return (
                  <ListItem
                    id={index.toString()}
                    onMouseEnter={onMouseEnter}
                    onMouseLeave={onMouseLeave}
                    key={index}
                  >
                    <ListItemText
                      style={{
                        fontFamily: defaultTheme.typography.subtitle2.fontFamily,
                        fontSize: defaultTheme.typography.htmlFontSize
                      }}
                      id={`text${index}`}
                      primary={value}

                    />
                  </ListItem>
                )
              })
            }
          </List>
          <Button
            variant="contained"
            color="error"
            startIcon={<LoginIcon />}
            style={Drawerstyles.containedBtn}
          >
            Sign in
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<PersonIcon />}
            style={Drawerstyles.outlineBtn}
          >
            Sign up
          </Button>

        </Box>
      </Drawer>
    </>
  );
};

export default CustomDrawer;