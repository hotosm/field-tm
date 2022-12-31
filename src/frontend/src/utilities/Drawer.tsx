import * as React from 'react';
import { Drawer } from 'rsuite';
import FacebookOfficialIcon from '@rsuite/icons/legacy/FacebookOfficial';
import { Box } from '@mui/system';
import { IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import OutlinedButton from './OutlinedButton';
import PersonIcon from '@mui/icons-material/Person';
import LoginIcon from '@mui/icons-material/Login';
import enviroment from '../enviroment';
const DrawerComponent = ({ open, placement, size, onClose }) => {



  const onMouseEnter = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element.style.color = `${enviroment.sysRedColor}`


  }
  const onMouseLeave = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element.style.color = `${enviroment.sysBlackColor}`
  }

  const style = {
    list: {
      width: '100%',
      bgcolor: 'background.paper',
    },
    listItem: {

      border: '1px solid lightgray'
    },
    outlineBtn: {
      fontSize: 14,
      padding: 8,
      width: '100%',
      marginTop: '4%',
      borderRadius: 7,
      fontFamily: 'BarlowMedium'


    },
    containedBtn: {
      fontSize: 14,
      padding: 8,
      width: '100%',
      marginTop: '0.7%',
      borderRadius: 7,
      fontFamily: 'BarlowMedium'
    }
  };

  return (
    <>
      <Drawer style={size == 'full' ? { width: '100%' } : { opacity: 1 }} size={size} placement={placement} open={open} onClose={onClose}>

        <Box sx={{ display: 'flex', flexDirection: 'column', padding: 3 }}>
          <Box sx={{ width: 50, borderRadius: '50%', marginLeft: '0.7%' }}>

            <IconButton
              size="large"
              aria-label="show more"
              aria-haspopup="true"
              onClick={onClose}
              color="inherit"

            >
              <CloseIcon />
            </IconButton>
          </Box>
          <Divider />
          <List sx={style.list} component="nav" aria-label="mailbox folders">
            {
              ['Explore Projects', 'My Contributions', 'Learn', 'About', 'Support'].map((value, index) => {
                return (
                  <ListItem id={index.toString()} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} key={index} button>
                    <ListItemText style={{ fontFamily: 'BarlowMedium' }} id={`text${index}`} primary={value} />
                  </ListItem>
                )
              })
            }
          </List>
          <OutlinedButton variant={'contained'} color={'error'} icon={<LoginIcon />} text="Sign in" style={style.containedBtn} />
          <OutlinedButton variant={'outlined'} color={'error'} icon={<PersonIcon />} text="Sign up" style={style.outlineBtn} />
        </Box>
      </Drawer>
    </>
  );
};

export default DrawerComponent;