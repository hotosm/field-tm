import React, { useEffect, useState } from 'react';
import windowDimention from '../../hooks/WindowDimension';
import CoreModules from '../../shared/CoreModules';
import AssetModules from '../../shared/AssetModules';
import { useNavigate } from 'react-router-dom';
import useForm from '../../hooks/useForm';
import CreateProjectValidation from './validation/CreateProjectValidation';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { OrganisationService } from '../../api/CreateProjectService';
import environment from '../../environment';
import { MenuItem, Select } from '@mui/material';
import { createPopup } from '../../utilfunctions/createPopup';

const ProjectDetailsForm: React.FC = () => {
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  // // const state:any = useSelector<any>(state=>state.project.projectData)
  // // console.log('state main :',state)

  // const { type } = windowDimention();
  // //get window dimension
  const navigate = useNavigate();

  const dispatch = CoreModules.useDispatch();
  // //dispatch function to perform redux state mutation

  const projectDetails: any = CoreModules.useSelector<any>((state) => state.createproject.projectDetails);
  // //we use use selector from redux to get all state of projectDetails from createProject slice

  const organizationListData: any = CoreModules.useSelector<any>((state) => state.createproject.organizationList);
  // //we use use selector from redux to get all state of projectDetails from createProject slice

  useEffect(() => {
    // dispatch(OrganisationService(`${environment.baseApiUrl}/organization/`));
  }, []);

  const submission = () => {
    // submitForm();
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(values));
    dispatch(CreateProjectActions.SetCreateProjectFormStep('upload-area'));
    navigate('/upload-area', { replace: true, state: { values: values } });
  };

  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    projectDetails,
    submission,
    CreateProjectValidation,
  );

  const inputFormStyles = () => {
    return {
      style: {
        color: defaultTheme.palette.error.main,
        fontFamily: defaultTheme.typography.fontFamily,
        fontSize: defaultTheme.typography.fontSize,
      }, // or className: 'your-class'
    };
  };
  // Changed OrganizationList Data into the Picker Component Format i.e label and value
  const organizationList = organizationListData.map((item) => ({ label: item.name, value: item.id }));

  // User has switched back to the tab
  const onFocus = () => {
    dispatch(OrganisationService(`${environment.baseApiUrl}/organization/`));
  };
  useEffect(() => {
    window.addEventListener('focus', onFocus);
    onFocus();
    // Calls onFocus when the window first loads
    return () => {
      window.removeEventListener('focus', onFocus);
      // window.removeEventListener("blur", onBlur);
    };
  }, []);
  return (
    <CoreModules.Stack sx={{ width: { xs: '95%' }, marginLeft: { md: '215px !important' } }}>
      <form onSubmit={handleSubmit} style={{ paddingBottom: '4rem' }}>
        <CoreModules.FormGroup>
          {/* Organization Dropdown For Create Project */}

          <CoreModules.FormControl sx={{ mb: 0, width: { md: '50%', lg: '30%' } }} variant="outlined">
            <CoreModules.Box
              sx={{
                display: 'flex',
                flexDirection: 'row',
                pt: 0,
              }}
            >
              <CoreModules.FormLabel
                component="h3"
                sx={{
                  '&.Mui-focused': {
                    color: 'black',
                  },
                }}
              >
                Organization
              </CoreModules.FormLabel>
              {/* </CoreModules.IconButton> */}
              <CoreModules.FormLabel
                component="h3"
                sx={{
                  color: 'red',
                  '&.Mui-focused': {
                    color: 'red',
                  },
                }}
              >
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            {/* <InputLabel id="demo-simple-select-label">Organization</InputLabel> */}
            <CoreModules.Stack
              sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center' }}
            >
              <Select
                inputProps={{ sx: { padding: '8.5px 14px' } }}
                sx={{
                  width: '100%',
                  '&.Mui-focused': {
                    border: '2px solid black',
                  },
                }}
                labelId="demo-simple-select-label"
                id="demo-simple-select"
                value={values.organization || ''}
                // label="Organization"
                onChange={(e) => {
                  handleCustomChange('organization', e.target.value);
                }}
              >
                {organizationList?.map((org) => (
                  <MenuItem key={org.value} value={org.value}>
                    {org.label}
                  </MenuItem>
                ))}
              </Select>
              <CoreModules.IconButton
                onClick={() => createPopup('Create Organization', 'createOrganization?popup=true')}
                sx={{ width: 'auto' }}
                // disabled={qrcode == "" ? true : false}
                color="info"
                aria-label="download qrcode"
              >
                <AssetModules.AddIcon
                  sx={{
                    fontSize: 25,
                    border: '1px solid',
                    borderRadius: '20px',
                    backgroundColor: defaultTheme.palette.success.main,
                    color: 'white',
                  }}
                />
              </CoreModules.IconButton>
            </CoreModules.Stack>
            {errors.organization && (
              <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                {errors.organization}
              </CoreModules.FormLabel>
            )}
          </CoreModules.FormControl>

          {/* END */}

          {/* Project Name Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 0, width: { md: '50%', lg: '30%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row', pt: 0 }}>
              <CoreModules.FormLabel component="h3">Central ODK Url</CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="url"
              name="url"
              type="url"
              autoComplete="on"
              label=""
              variant="outlined"
              inputProps={{ sx: { padding: '8.5px 14px' } }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              value={values.odk_central_url}
              onChange={(e) => {
                handleCustomChange('odk_central_url', e.target.value);
              }}
              helperText={errors.odk_central_url}
              FormHelperTextProps={inputFormStyles()}
            />
            {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
          </CoreModules.FormControl>
          {/* END */}

          {/* Project Name Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 1, width: { md: '50%', lg: '30%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel sx={{}} component="h3">
                Central ODK Email/Username
              </CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="odk_central_name"
              name="username"
              label=""
              variant="outlined"
              inputProps={{ sx: { padding: '8.5px 14px' } }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              value={values.odk_central_user}
              onChange={(e) => {
                handleCustomChange('odk_central_user', e.target.value);
              }}
              autoComplete="on"
              helperText={errors.odk_central_user}
              FormHelperTextProps={inputFormStyles()}
            />
            {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
          </CoreModules.FormControl>
          {/* END */}

          {/* Project Name Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 1, width: { md: '50%', lg: '30%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel component="h3">Central ODK Password </CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="odk_central_new_password"
              label=""
              variant="outlined"
              inputProps={{ sx: { padding: '8.5px 14px' } }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              value={values.odk_central_password}
              type="password"
              autoComplete="on"
              onChange={(e) => {
                handleCustomChange('odk_central_password', e.target.value);
              }}
              helperText={errors.odk_central_password}
              FormHelperTextProps={inputFormStyles()}
            />
            {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
          </CoreModules.FormControl>
          {/* END */}
          {/* Project Name Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 3, width: { md: '50%', lg: '30%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel component="h3">Project Name</CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="project_name"
              label=""
              variant="outlined"
              inputProps={{ sx: { padding: '8.5px 14px' } }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              value={values.name}
              onChange={(e) => {
                handleCustomChange('name', e.target.value);
              }}
              helperText={errors.name}
              FormHelperTextProps={inputFormStyles()}
            />
            {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
          </CoreModules.FormControl>
          {/* END */}

          {/* Project Name Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 0, width: { md: '50%', lg: '30%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row', pt: 0 }}>
              <CoreModules.FormLabel component="h3">Hashtag</CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="hashtags"
              name="hashtags"
              type="hashtags"
              autoComplete="on"
              label=""
              variant="outlined"
              inputProps={{ sx: { padding: '8.5px 14px' } }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              value={values.hashtags}
              onChange={(e) => {
                handleCustomChange('hashtags', e.target.value);
              }}
              helperText={errors.odk_central_url}
              FormHelperTextProps={inputFormStyles()}
            />
            {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
          </CoreModules.FormControl>
          {/* END */}

          {/* Short Description Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 3, width: { md: '50%', lg: '50%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel component="h3">Short Description</CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="short_description"
              label=""
              variant="outlined"
              value={values.short_description}
              onChange={(e) => {
                handleCustomChange('short_description', e.target.value);
              }}
              multiline
              rows={4}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              helperText={errors.short_description}
              FormHelperTextProps={inputFormStyles()}
            />
          </CoreModules.FormControl>
          {/* END */}

          {/* Description Form Input For Create Project */}
          <CoreModules.FormControl sx={{ mb: 3, width: { md: '50%', lg: '50%' } }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel component="h3">Description</CoreModules.FormLabel>
              <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                *
              </CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.TextField
              id="description"
              label=""
              variant="outlined"
              value={values.description}
              onChange={(e) => {
                handleCustomChange('description', e.target.value);
              }}
              multiline
              rows={4}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: 'black',
                  },
                },
              }}
              helperText={errors.description}
              FormHelperTextProps={inputFormStyles()}
            />
          </CoreModules.FormControl>
          {/* END */}

          <CoreModules.Box
            sx={{
              display: 'flex',
              width: { xs: 'full', md: '50%' },
              justifyContent: 'center',
            }}
          >
            {/* Form Submission Button For Create Project */}
            <CoreModules.Button variant="contained" color="error" sx={{ width: '10%' }} type="submit">
              Next
            </CoreModules.Button>
            {/* END */}
          </CoreModules.Box>
        </CoreModules.FormGroup>
      </form>
    </CoreModules.Stack>
  );
};
export default ProjectDetailsForm;
