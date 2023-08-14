import React from 'react';
import CoreModules from '../../shared/CoreModules.js';
import useForm from '../../hooks/useForm';
import OrganizationAddValidation from './Validation/OrganizationAddValidation';
import { MenuItem, Select } from '@mui/material';
import { OrganizationService } from '../../api/OrganizationService';
import environment from '../../environment';

const formData = {};
const organizationTypeList = ['FREE', 'DISCOUNTED', 'FULL_FEE'];
const organizationDataList = organizationTypeList.map((item, index) => ({ label: item, value: index + 1 }));
const OrganizationAddForm = () => {
  const dispatch = CoreModules.useAppDispatch();
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);

  const submission = () => {
    // eslint-disable-next-line no-use-before-define
    // submitForm();
    dispatch(OrganizationService(`${environment.baseApiUrl}/organization/`, values));
    // navigate("/select-form", { replace: true, state: { values: values } });
  };
  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    formData,
    submission,
    OrganizationAddValidation,
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
  return (
    <form onSubmit={handleSubmit} style={{ height: '100%' }}>
      <CoreModules.FormGroup sx={{ height: '100%', overflow: 'scroll', flexWrap: 'nowrap' }}>
        <CoreModules.Typography
          variant="subtitle2"
          sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}
        >
          Add Organization
        </CoreModules.Typography>
        {/* Organization Name Form Input For Create Project */}
        <CoreModules.FormControl sx={{ mb: 0, width: '100%' }}>
          <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row', pt: 0 }}>
            <CoreModules.FormLabel component="h3">Name</CoreModules.FormLabel>
            <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
              *
            </CoreModules.FormLabel>
          </CoreModules.Box>
          <CoreModules.TextField
            id="name"
            label=""
            variant="filled"
            inputProps={{ sx: { padding: '8.5px 14px' } }}
            value={values.name}
            onChange={(e) => {
              handleCustomChange('name', e.target.value);
            }}
            helperText={errors.name}
            FormHelperTextProps={inputFormStyles()}
          />
          {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
        </CoreModules.FormControl>
        <CoreModules.FormControl sx={{ mb: 0, width: '100%' }}>
          <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row', pt: 0 }}>
            <CoreModules.FormLabel component="h3">Website</CoreModules.FormLabel>
            <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
              *
            </CoreModules.FormLabel>
          </CoreModules.Box>
          <CoreModules.TextField
            id="url"
            label=""
            variant="filled"
            inputProps={{ sx: { padding: '8.5px 14px' } }}
            value={values.url}
            onChange={(e) => {
              handleCustomChange('url', e.target.value);
            }}
            helperText={errors.url}
            FormHelperTextProps={inputFormStyles()}
          />
          {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
        </CoreModules.FormControl>
        {/* Description Form Input For Create Project */}
        <CoreModules.FormControl sx={{ mb: 3 }}>
          <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
            <CoreModules.FormLabel component="h3">Description</CoreModules.FormLabel>
            <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
              *
            </CoreModules.FormLabel>
          </CoreModules.Box>
          <CoreModules.TextField
            id="description"
            label=""
            variant="filled"
            value={values.description}
            onChange={(e) => {
              handleCustomChange('description', e.target.value);
            }}
            multiline
            rows={4}
            helperText={errors.description}
            FormHelperTextProps={inputFormStyles()}
          />
        </CoreModules.FormControl>
        {/* END */}
        <CoreModules.FormControl sx={{ mb: 0, width: '50%' }}>
          <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row', pt: 0 }}>
            <CoreModules.FormLabel component="h3">Logo</CoreModules.FormLabel>
            <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
              *
            </CoreModules.FormLabel>
          </CoreModules.Box>
          <CoreModules.TextField
            id="logo"
            label=""
            variant="filled"
            inputProps={{ sx: { padding: '8.5px 14px' } }}
            value={values.logo}
            onChange={(e) => {
              handleCustomChange('logo', e.target.value);
            }}
            helperText={errors.logo}
            FormHelperTextProps={inputFormStyles()}
          />
          {/* <CoreModules.FormLabel component="h3" sx={{ display:'flex'}}>{errors.name} <CoreModules.FormLabel component="h4" sx={{color:'red'}}>*</CoreModules.FormLabel></CoreModules.FormLabel> */}
        </CoreModules.FormControl>

        <CoreModules.FormControl sx={{ mb: 0, width: '100%' }} variant="filled">
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
              Type
            </CoreModules.FormLabel>
            {/* </CoreModules.IconButton> */}
            <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
              *
            </CoreModules.FormLabel>
          </CoreModules.Box>
          {/* <InputLabel id="demo-simple-select-label">Organization</InputLabel> */}
          <CoreModules.Stack
            sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center' }}
          >
            <Select
              sx={{ width: '100%' }}
              labelId="demo-simple-select-label"
              id="demo-simple-select"
              value={values.type || ''}
              label="Organization Type"
              onChange={(e) => {
                handleCustomChange('type', e.target.value);
                // dispatch(CreateProjectActions.SetProjectDetails({ key: 'organization', value: e.target.value }))
              }}
            >
              {organizationDataList?.map((org) => <MenuItem value={org.value}>{org.label}</MenuItem>)}
            </Select>
          </CoreModules.Stack>
          {errors.type && (
            <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
              {errors.type}
            </CoreModules.FormLabel>
          )}
        </CoreModules.FormControl>

        {/* END */}
      </CoreModules.FormGroup>
      <CoreModules.Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <CoreModules.Button
          variant="contained"
          color="error"
          type="submit"
          sx={{ width: '20%' }}
          // disabled={!fileUpload ? true : false}
          onClick={() => {
            // onCreateProjectSubmission();
          }}
        >
          Submit
        </CoreModules.Button>
      </CoreModules.Box>
    </form>
  );
};

OrganizationAddForm.propTypes = {};

export default OrganizationAddForm;
