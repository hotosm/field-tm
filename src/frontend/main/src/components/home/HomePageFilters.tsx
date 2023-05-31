import React from 'react';
import windowDimention from '../../hooks/WindowDimension';
import CustomDropdown from '../../utilities/CustomDropdown';
import CoreModules from '../../shared/CoreModules';
import AssetModules from '../../shared/AssetModules';

const organizationTypeList = ['FREE', 'DISCOUNTED', 'FULL_FEE'];
const organizationDataList = organizationTypeList.map((item, index) => ({ label: item, value: index + 1 }));

//Home Filter
const HomePageFilters = () => {
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  const token: any = CoreModules.useSelector<any>((state) => state.login.loginToken);
  const { windowSize } = windowDimention();
  const searchableInnerStyle: any = {
    toolbar: {
      marginTop: '0.7%',
      width: 250,
      fontFamily: defaultTheme.typography.h3.fontFamily,
      fontSize: defaultTheme.typography.h3.fontSize,
    },
    outlineBtn: {
      width: 250,
      marginTop: '0.7%',
      borderRadius: 7,
      fontFamily: defaultTheme.typography.h3.fontFamily,
      fontSize: defaultTheme.typography.h3.fontSize,
    },
    outlineBtnXs: {
      width: '50%',
      borderRadius: 7,
      fontFamily: defaultTheme.typography.h3.fontFamily,
      fontSize: defaultTheme.typography.h3.fontSize,
    },
    toolbarXs: {
      width: '50%',
      fontFamily: defaultTheme.typography.h3.fontFamily,
      fontSize: defaultTheme.typography.h3.fontSize,
    },
  };

  const Search = AssetModules.styled('div')(({ theme }) => ({
    position: 'relative',
    borderRadius: theme.shape.borderRadius,
    backgroundColor: AssetModules.alpha(theme.palette.common.white, 0.15),
    '&:hover': {
      backgroundColor: AssetModules.alpha(theme.palette.common.white, 0.25),
    },
    marginRight: theme.spacing(2),
    marginLeft: 0,
    opacity: 0.8,
    border: `1px solid ${theme.palette.info['main']}`,
    width: '100%',
    [theme.breakpoints.up('sm')]: {
      marginLeft: theme.spacing(3),
      width: 'auto',
    },
  }));

  const SearchIconWrapper = AssetModules.styled('div')(({ theme }) => ({
    padding: theme.spacing(0, 2),
    height: '100%',
    position: 'absolute',
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  }));

  const StyledInputBase = AssetModules.styled(CoreModules.InputBase)(({ theme }) => ({
    color: 'primary',
    '& .MuiInputBase-input': {
      padding: theme.spacing(1, 1, 1, 0),
      fontFamily: theme.typography.h3.fontFamily,
      // vertical padding + font size from searchIcon
      paddingLeft: `calc(1em + ${theme.spacing(4)})`,
      transition: theme.transitions.create('width'),
      width: '100%',
      [theme.breakpoints.up('md')]: {
        width: '20ch',
      },
    },
  }));

  return (
    <CoreModules.Stack>
      {/* Explore project typography in mobile size */}
      <CoreModules.Stack
        sx={{ display: { xs: windowSize.width <= 599 ? 'flex' : 'none', md: 'none' }, justifyContent: 'center' }}
      >
        <CoreModules.Typography variant="subtitle2" noWrap mt={'2%'} ml={'3%'}>
          EXPLORE PROJECTS
        </CoreModules.Typography>
      </CoreModules.Stack>
      {/* <======End======> */}

      {/* full Searchables container in md,lg,xl size */}
      <CoreModules.Stack
        sx={{ display: { xs: 'none', md: 'flex' } }}
        direction={'row'}
        spacing={2}
        justifyContent="center"
      >
        {/* <CoreModules.Button
                    variant="outlined"
                    color="error"
                    startIcon={<AssetModules.AutoAwesome />}
                    style={searchableInnerStyle.outlineBtn}
                >
                    Filters
                </CoreModules.Button> */}

        <CustomDropdown
          color={'red'}
          appearance={'ghost'}
          names={[
            'Urgent Projects',
            'Active Projects',
            'New Projects',
            'Old Projects',
            'Easy Projects',
            'Challenging Projects',
          ]}
          toolBarStyle={searchableInnerStyle.toolbar}
          text={'SORT BY'}
          size={'lg'}
        />
      </CoreModules.Stack>
      {/* Create New Project Button  */}
      <CoreModules.Stack
        sx={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: '3rem',
          gap: 5,
        }}
      >
        <CoreModules.FormControl size="small" sx={{ m: 1, minWidth: 120, width: 250 }} margin="normal">
          <CoreModules.InputLabel
            id="demo-simple-select-helper-label"
            sx={{
              '&.Mui-focused': {
                color: defaultTheme.palette.black,
              },
            }}
          >
            Projects
          </CoreModules.InputLabel>
          <CoreModules.Select
            labelId="demo-simple-select-helper-label"
            id="demo-simple-select-helper"
            value="dropdown"
            label="Age"
          >
            {organizationDataList?.map((org) => (
              <CoreModules.MenuItem value={org.value}>{org.label}</CoreModules.MenuItem>
            ))}
          </CoreModules.Select>
        </CoreModules.FormControl>
        <Search id="search">
          <SearchIconWrapper>
            <AssetModules.SearchIcon color="info" />
          </SearchIconWrapper>
          <StyledInputBase placeholder="Search…" inputProps={{ 'aria-label': 'search' }} style={{ width: '100%' }} />
        </Search>
        <CoreModules.Link
          to={'/create-project'}
          style={{
            //   marginLeft: '3%',
            textDecoration: 'none',
            // color: defaultTheme.palette.info.main,
          }}
        >
          <CoreModules.Button
            variant="outlined"
            color="error"
            startIcon={<AssetModules.AddIcon />}
            style={searchableInnerStyle.outlineBtn}
            // disabled={token == null}
          >
            Create New Project
          </CoreModules.Button>
        </CoreModules.Link>
        {/* <======End======> */}
      </CoreModules.Stack>
      {/* <======End======> */}

      {/* Search field in mobile size */}
      <CoreModules.Stack
        sx={{ display: { xs: 'flex', md: 'none', flexDirection: 'column', justifyContent: 'center' } }}
      >
        <Search id="searchXs">
          <SearchIconWrapper>
            <AssetModules.SearchIcon />
          </SearchIconWrapper>
          <StyledInputBase placeholder="Search…" inputProps={{ 'aria-label': 'search' }} style={{ width: '100%' }} />
        </Search>
      </CoreModules.Stack>
      {/* <======End======> */}

      {/* filter and sort button in mobile size */}
      <CoreModules.Stack
        spacing={1}
        mt={'2%'}
        mb={'2%'}
        direction={'row'}
        sx={{ display: { xs: 'flex', md: 'none' }, width: '100%', justifyContent: 'center' }}
      >
        <CoreModules.Button
          variant="outlined"
          color="error"
          startIcon={<AssetModules.AutoAwesome />}
          style={searchableInnerStyle.outlineBtnXs}
        >
          Filters
        </CoreModules.Button>
        <CustomDropdown
          color={'red'}
          appearance={'ghost'}
          names={[
            'Urgent Projects',
            'Active Projects',
            'New Projects',
            'Old Projects',
            'Easy Projects',
            'Challenging Projects',
          ]}
          toolBarStyle={searchableInnerStyle.toolbarXs}
          text={'SORT BY'}
          size={'lg'}
        />
      </CoreModules.Stack>
      {/* <======End======> */}
    </CoreModules.Stack>
  );
};

export default HomePageFilters;
