import React, { useEffect } from 'react';
import CoreModules from '@/shared/CoreModules';
import environment from '@/environment';
import useForm from '@/hooks/useForm';
import OrganisationAddValidation from '@/components/organisation/Validation/OrganisationAddValidation';
import { PostOrganisationDataService } from '@/api/OrganisationService';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { OrganisationAction } from '@/store/slices/organisationSlice';

const CreateOrganisationForm = () => {
  const dispatch = CoreModules.useAppDispatch();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const postOrganisationData: any = CoreModules.useAppSelector((state) => state.organisation.postOrganisationData);

  const organisationFormData: any = CoreModules.useAppSelector((state) => state.organisation.organisationFormData);

  const submission = () => {
    dispatch(PostOrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation/`, values));
  };
  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    organisationFormData,
    submission,
    OrganisationAddValidation,
  );
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
    if (postOrganisationData) {
      dispatch(OrganisationAction.postOrganisationData(null));
      dispatch(OrganisationAction.SetOrganisationFormData({}));
      if (searchParams.get('popup') === 'true') {
        window.close();
      } else {
        navigate('/organisation');
      }
    }
  }, [postOrganisationData]);

  return (
    <CoreModules.Box
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#f0efef', flex: 1, gap: 3 }}
    >
      <div className="fmtm-pt-[5%] sm:fmtm-pt-[2%] fmtm-w-full fmtm-flex fmtm-justify-center">
        <h1 className="fmtm-text-xl sm:fmtm-text-2xl md:fmtm-text-4xl fmtm-font-bold">CREATE NEW ORGANIZATION</h1>
      </div>
      <CoreModules.Box
        sx={{
          width: '85%',
          maxWidth: 600,
          padding: 3,
          cursor: 'pointer',
          background: '#ffff',
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
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel sx={{}} component="h3">
                  ODK Central URL (Optional)
                </CoreModules.FormLabel>
              </CoreModules.Box>
              <CoreModules.TextField
                id="odk_central_url"
                label=""
                variant="filled"
                value={values.odk_central_url}
                onChange={(e) => {
                  handleCustomChange('odk_central_url', e.target.value);
                }}
                fullWidth
                multiline
                rows={1}
                helperText={errors.odk_central_url}
                FormHelperTextProps={inputFormStyles()}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel sx={{}} component="h3">
                  ODK Central User (Optional)
                </CoreModules.FormLabel>
              </CoreModules.Box>
              <CoreModules.TextField
                id="odk_central_user"
                label=""
                variant="filled"
                value={values.odk_central_user}
                onChange={(e) => {
                  handleCustomChange('odk_central_user', e.target.value);
                }}
                fullWidth
                multiline
                rows={1}
                helperText={errors.odk_central_user}
                FormHelperTextProps={inputFormStyles()}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.FormLabel sx={{}} component="h3">
                  ODK Central Password (Optional)
                </CoreModules.FormLabel>
              </CoreModules.Box>
              <CoreModules.TextField
                id="odk_central_password"
                label=""
                variant="filled"
                value={values.odk_central_password}
                onChange={(e) => {
                  handleCustomChange('odk_central_password', e.target.value);
                }}
                fullWidth
                multiline
                rows={1}
                helperText={errors.odk_central_password}
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

export default CreateOrganisationForm;
