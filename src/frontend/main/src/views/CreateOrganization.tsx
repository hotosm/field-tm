import React, { useState } from 'react';
import { InputLabel } from '@mui/material';
import CoreModules from '../shared/CoreModules';
import environment from '../environment';
import useForm from '../hooks/useForm';
import { useDispatch } from 'react-redux';
import OrganizationAddValidation from '../components/organization/Validation/OrganizationAddValidation';
import { PostOrganizationDataService } from '../api/OrganizationService';

const formData = {};
const organizationTypeList = ['FREE', 'DISCOUNTED', 'FULL_FEE'];
const organizationDataList = organizationTypeList.map((item, index) => ({ label: item, value: index + 1 }));
const CreateOrganizationForm = () => {
  const dispatch = useDispatch();
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);

  const submission = () => {
    dispatch(PostOrganizationDataService(`${environment.baseApiUrl}/projects/organization/`, values));
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
    <CoreModules.Box
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'start', background: '#f0efef', flex: 1, gap: 3 }}
    >
      <CoreModules.Box
        sx={{
          paddingTop: '2%',
          justifyContent: 'flex-start',
          marginLeft: '7.5%',
        }}
      >
        <CoreModules.Typography variant="condensed">CREATE NEW ORGANIZATION</CoreModules.Typography>
      </CoreModules.Box>
      <CoreModules.Box
        sx={{
          width: 600,
          padding: 5,
          cursor: 'pointer',
          background: '#ffff',
          marginLeft: '7.5%',
          borderRadius: 2,
        }}
      >
        <form onSubmit={handleSubmit}>
          <CoreModules.TextField
            id="name"
            variant="filled"
            label="Organization Name"
            fullWidth
            margin="normal"
            value={values.name}
            onChange={(e) => {
              handleCustomChange('name', e.target.value);
            }}
            helperText={errors.name}
            FormHelperTextProps={inputFormStyles()}
          />
          <CoreModules.TextField
            id="url"
            label="Website"
            value={values.url}
            variant="filled"
            margin="normal"
            onChange={(e) => {
              handleCustomChange('url', e.target.value);
            }}
            fullWidth
            helperText={errors.url}
            FormHelperTextProps={inputFormStyles()}
          />
          <CoreModules.TextField
            id="description"
            label=""
            variant="filled"
            value={values.description}
            onChange={(e) => {
              handleCustomChange('description', e.target.value);
            }}
            fullWidth
            multiline
            rows={4}
            helperText={errors.description}
            FormHelperTextProps={inputFormStyles()}
          />
          <CoreModules.FormControl fullWidth margin="normal">
            <InputLabel id="dropdown-label">Dropdown</InputLabel>
            <CoreModules.Select
              labelId="dropdown-label"
              id="type"
              value={values.type || ''}
              onChange={(e) => {
                handleCustomChange('type', e.target.value);
              }}
            >
              {organizationDataList?.map((org) => (
                <CoreModules.MenuItem value={org.value}>{org.label}</CoreModules.MenuItem>
              ))}
            </CoreModules.Select>
            {errors.type && (
              <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                {errors.type}
              </CoreModules.FormLabel>
            )}
          </CoreModules.FormControl>
          <CoreModules.Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <CoreModules.TextField
              id="logo"
              type="file"
              variant="filled"
              value={values.logo}
              onChange={(e) => {
                handleCustomChange('logo', e.target.value);
              }}
              inputProps={{ accept: 'image/*' }}
              style={{ display: 'none' }}
              helperText={errors.logo}
              FormHelperTextProps={inputFormStyles()}
            />
            <label htmlFor="logo">
              <CoreModules.Button variant="contained" component="span">
                Choose Logo
              </CoreModules.Button>
            </label>
            {errors.logo && (
              <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                {errors.logo}
              </CoreModules.FormLabel>
            )}
          </CoreModules.Box>
          <CoreModules.Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <CoreModules.Button
              type="submit"
              variant="outlined"
              color="error"
              size="large"
              sx={{ minWidth: 'fit-content', width: 'auto', fontWeight: 'bold' }}
            >
              Submit
            </CoreModules.Button>
          </CoreModules.Box>
        </form>
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default CreateOrganizationForm;
