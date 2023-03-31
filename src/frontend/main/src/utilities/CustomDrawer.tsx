import * as React from "react";
import { Drawer } from "rsuite";
import CoreModules from "../shared/CoreModules";
import AssetModules from "../shared/AssetModules";
import { NavLink } from "react-router-dom";

const CustomDrawer = ({ open, placement, size, onClose,onSignOut }) => {
  const defaultTheme: any = CoreModules.useSelector<any>(
    (state) => state.theme.hotTheme
  );
  const onMouseEnter = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element != null
      ? (element.style.color = `${defaultTheme.palette.error["main"]}`)
      : null;
  };
  const token = CoreModules.useSelector<any>(state=>state.login.loginToken)
  const onMouseLeave = (event) => {
    const element: any = document.getElementById(`text${event.target.id}`);
    element != null
      ? (element.style.color = `${defaultTheme.palette.info["main"]}`)
      : null;
  };


  const Drawerstyles = {
    list: {
      width: "100%",
      bgcolor: "background.paper",
    },
    outlineBtn: {
      padding: 8,
      width: "100%",
      marginTop: "4%",
      borderRadius: 7,
      fontFamily: defaultTheme.typography.subtitle2.fontFamily,
    },
    containedBtn: {
      padding: 8,
      width: "100%",
      marginTop: "0.7%",
      borderRadius: 7,
      fontFamily: defaultTheme.typography.subtitle2.fontFamily,
    },
  };

  const MenuItems = [
    {
      name: "Explore Projects",
      ref: "/explore",
      isExternalLink: false,
      isActive: true,
    },
    {
      name: "My Contributions",
      ref: "TBD",
      isExternalLink: false,
      isActive: false,
    },
    {
      name: "Learn",
      ref: "https://github.com/hotosm/fmtm/wiki",
      isExternalLink: true,
      isActive: true,
    },
    {
      name: "About",
      ref: "https://github.com/hotosm/fmtm/wiki",
      isExternalLink: true,
      isActive: true,
    },
    {
      name: "Support",
      ref: "https://github.com/hotosm/fmtm/issues/",
      isExternalLink: true,
      isActive: true,
    },
  ];

  return (
    <>
      <Drawer
        style={size == "full" ? { width: "100%" } : { opacity: 1 }}
        size={size}
        placement={placement}
        open={open}
        onClose={onClose}
      >
        <CoreModules.Stack
          sx={{ display: "flex", flexDirection: "column", padding: 3 }}
        >
          <CoreModules.Stack
            sx={{ width: 50, borderRadius: "50%", marginLeft: "0.7%" }}
          >
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

          <CoreModules.Divider color={'info'} />
          {
            token !=null &&
            <CoreModules.Stack direction={'row'} justifyContent={'center'}  ml={'3%'} spacing={1}>
            <AssetModules.PersonIcon color='success' sx={{ display: { xs: 'block', md: 'none'},mt:'1%' }} />
            <CoreModules.Typography
                variant="subtitle2"
                color={'info'}
                noWrap
                sx={{ display: { xs: 'block', md: 'none', } }}
               
              >
                {token['username']}
              </CoreModules.Typography>
          </CoreModules.Stack>
          }
          <CoreModules.Divider color={'info'} />
          <CoreModules.List
            sx={Drawerstyles.list}
            component="nav"
            aria-label="mailStack folders"
          >
            {MenuItems.filter((menuItem) => menuItem.isActive).map(
              (menuDetails, index) =>
                menuDetails.isExternalLink ? (
                  <a
                    href={menuDetails.ref}
                    style={{
                      textDecoration: "inherit",
                      color: "inherit",
                      fontFamily: "inherit",
                      fontWeight: 400,
                      fontSize: "1.01587rem",
                      background: "#000000",
                      opacity: 0.8,
                    }}
                  >
                    <CoreModules.ListItem
                      id={index.toString()}
                      onMouseEnter={onMouseEnter}
                      onMouseLeave={onMouseLeave}
                      key={index}
                    >
                      <CoreModules.ListItemText
                        id={`text${index}`}
                        primary={menuDetails.name}
                      />
                    </CoreModules.ListItem>
                  </a>
                ) : (
                  <NavLink
                    to={menuDetails.ref}
                    style={{
                      textDecoration: "inherit",
                      color: "inherit",
                      fontFamily: "inherit",
                      fontSize: "1.01587rem",
                      background: "#000000",
                      opacity: 0.8,
                    }}
                  >
                    <CoreModules.ListItem
                      id={index.toString()}
                      onMouseEnter={onMouseEnter}
                      onMouseLeave={onMouseLeave}
                      key={index}
                    >
                      <CoreModules.ListItemText
                        id={`text${index}`}
                        primary={menuDetails.name}
                      />
                    </CoreModules.ListItem>
                  </NavLink>
                )
            )}
          </CoreModules.List>
          <CoreModules.Stack sx={{display:{xs:'flex',md:'none'}}}>
              {
                token != null?
                <CoreModules.Link  style={{textDecoration:'none'}} to={"/"}>
                <CoreModules.Button
                  onClick={onSignOut}
                  variant="contained"
                  color="error"
                  startIcon={<AssetModules.ExitToAppIcon />}
                  style={Drawerstyles.containedBtn}
                
                > 
                  Sign Out
                </CoreModules.Button>
              </CoreModules.Link>
              :
              <CoreModules.Link  style={{textDecoration:'none'}} to={"/login"}>
              <CoreModules.Button
                onClick={onClose}
                variant="contained"
                color="error"
                startIcon={<AssetModules.LoginIcon />}
                style={Drawerstyles.containedBtn}
              
              > 
                Sign in
              </CoreModules.Button>
            </CoreModules.Link>
              }
              <CoreModules.Link  style={{textDecoration:'none'}} to={"/signup"}>
                <CoreModules.Button
                  onClick={onClose}
                  variant="outlined"
                  color="error"
                  startIcon={<AssetModules.PersonIcon />}
                  style={Drawerstyles.outlineBtn}
                >
                  Sign up
                </CoreModules.Button>
              </CoreModules.Link >
          </CoreModules.Stack>
        </CoreModules.Stack>
      </Drawer>
    </>
  );
};

export default CustomDrawer;
