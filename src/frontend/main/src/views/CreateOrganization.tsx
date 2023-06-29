import React, { useEffect, useState } from 'react';
import CoreModules from '../shared/CoreModules';
import environment from '../environment';
import useForm from '../hooks/useForm';
import { useDispatch } from 'react-redux';
import OrganizationAddValidation from '../components/organization/Validation/OrganizationAddValidation';
import { PostOrganizationDataService } from '../api/OrganizationService';
import { useNavigate } from 'react-router-dom';
import { OrganizationAction } from '../store/slices/organizationSlice';


const CreateOrganizationForm = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const defaultTheme: any = CoreModules.useSelector<any>((state) => state.theme.hotTheme);
  const postOrganizationData: any = CoreModules.useSelector<any>((state) => state.organization.postOrganizationData);
  const postOrganizationDataLoading: any = CoreModules.useSelector<any>((state) => state.organization.postOrganizationDataLoading);
  const organizationFormData: any = CoreModules.useSelector<any>((state) => state.organization.organizationFormData);

  const submission = () => {
    dispatch(PostOrganizationDataService(`${environment.baseApiUrl}/organization/`, values));
  };
  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    organizationFormData,
    submission,
    OrganizationAddValidation,
  );
    console.log(values,'values');
  const inputFormStyles = () => {
    return {
      style: {
        color: defaultTheme.palette.error.main,
        fontFamily: defaultTheme.typography.fontFamily,
        fontSize: defaultTheme.typography.fontSize,
      },
    };
  };

  useEffect(() => {
    if (postOrganizationData) {

      navigate('/organization');
      dispatch(OrganizationAction.postOrganizationData(null))
      dispatch(OrganizationAction.SetOrganizationFormData({}))
    }


  }, [postOrganizationData])


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
          padding: 3,
          cursor: 'pointer',
          background: '#ffff',
          marginLeft: '7.5%',
          borderRadius: 2,
        }}
      >
        <form onSubmit={handleSubmit}>
          <CoreModules.FormGroup>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel component="h3">Organization Name</CoreModules.FormLabel>
                <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                  *
                </CoreModules.FormLabel>
              </CoreModules.Box>

              <CoreModules.TextField
                id="name"
                variant="filled"
                fullWidth
                margin="normal"
                value={values.name}
                onChange={(e) => {
                  handleCustomChange('name', e.target.value);
                }}
                helperText={errors.name}
                FormHelperTextProps={inputFormStyles()}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel sx={{}} component="h3">
                  Website URL
                </CoreModules.FormLabel>
                <CoreModules.FormLabel component="h3" sx={{ color: 'red' }}>
                  *
                </CoreModules.FormLabel>
              </CoreModules.Box>
              <CoreModules.TextField
                id="url"
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
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel sx={{}} component="h3">
                  Description
                </CoreModules.FormLabel>
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
                fullWidth
                multiline
                rows={4}
                helperText={errors.description}
                FormHelperTextProps={inputFormStyles()}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl fullWidth margin="normal" variant="filled" sx={{ gap: 1 }}>
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
                  Upload Logo
                </CoreModules.FormLabel>
                
              </CoreModules.Box>
              <CoreModules.Button variant="contained" component="span">
                <CoreModules.Input
                  type="file"
                  onChange={(e) => {
                    handleCustomChange('logo', e.target?.files?.[0]);
                  }}
                />
              </CoreModules.Button>

              {errors.logo && (
                <CoreModules.FormLabel component="h3" sx={{ color: defaultTheme.palette.error.main }}>
                  {errors.logo}
                </CoreModules.FormLabel>
              )}
            </CoreModules.FormControl>
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
          </CoreModules.FormGroup>
        </form>
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default CreateOrganizationForm;
