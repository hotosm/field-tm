import React, { useEffect } from 'react';
import CoreModules from '@/shared/CoreModules';
import environment from '@/environment';
import useForm from '@/hooks/useForm';
import InputTextField from '@/components/common/InputTextField';
import TextArea from '@/components/common/TextArea';
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
        <form
          className="xl:fmtm-w-[83%] lg:fmtm-h-[60vh] xl:fmtm-h-[58vh] fmtm-bg-white fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar"
          onSubmit={handleSubmit}
        >
          <CoreModules.FormGroup className="fmtm-flex fmtm-flex-col fmtm-gap-6 md:fmtm-w-[50%]">
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <InputTextField
                id="name"
                name="name"
                label="Organization Name"
                value={values.name}
                onChange={(e) => {
                  handleCustomChange('name', e.target.value);
                }}
                fieldType="text"
                required
                errorMsg={errors.name}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <InputTextField
                id="url"
                name="url"
                label="Website URL"
                value={values.url}
                onChange={(e) => {
                  handleCustomChange('url', e.target.value);
                }}
                fieldType="text"
                required
                errorMsg={errors.url}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <TextArea
                id="description"
                name="description"
                label="Description"
                rows={3}
                value={values.description}
                onChange={(e) => {
                  handleCustomChange('description', e.target.value);
                }}
                required
                errorMsg={errors.description}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <InputTextField
                id="odk_central_url"
                name="odk_central_url"
                label="ODK Central URL (Optional)"
                value={values.odk_central_url}
                onChange={(e) => {
                  handleCustomChange('odk_central_url', e.target.value);
                }}
                fieldType="text"
                errorMsg={errors.odk_central_url}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <InputTextField
                id="odk_central_user"
                name="odk_central_user"
                label="ODK Central User (Optional)"
                value={values.odk_central_user}
                onChange={(e) => {
                  handleCustomChange('odk_central_user', e.target.value);
                }}
                fieldType="text"
                errorMsg={errors.odk_central_user}
              />
            </CoreModules.FormControl>
            <CoreModules.FormControl sx={{ width: '100%' }}>
              <InputTextField
                id="odk_central_password"
                name="odk_central_password"
                label="ODK Central Password (Optional)"
                value={values.odk_central_password}
                onChange={(e) => {
                  handleCustomChange('odk_central_password', e.target.value);
                }}
                fieldType="password"
                errorMsg={errors.odk_central_password}
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
                    fontWeight: 'bold',
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
