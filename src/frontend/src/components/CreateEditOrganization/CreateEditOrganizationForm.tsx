import React, { useEffect } from 'react';
import Button from '@/components/common/Button';
import InputTextField from '@/components/common/InputTextField';
import TextArea from '@/components/common/TextArea';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import useForm from '@/hooks/useForm';
import OrganizationDetailsValidation from '@/components/CreateEditOrganization/validation/OrganizationDetailsValidation';
import RadioButton from '@/components/common/RadioButton';
import { PatchOrganizationDataService, PostOrganisationDataService } from '@/api/OrganisationService';
import { diffObject } from '@/utilfunctions/compareUtils';
import { radioOptionsType } from '@/models/organisation/organisationModel';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import UploadArea from '@/components/common/UploadArea';
import { CommonActions } from '@/store/slices/CommonSlice';
import { CustomCheckbox } from '@/components/common/Checkbox';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const API_URL = import.meta.env.VITE_API_URL;

const organizationTypeOptions: radioOptionsType[] = [
  { name: 'osm_community', value: 'OSM_COMMUNITY', label: 'OSM Community' },
  { name: 'company', value: 'COMPANY', label: 'Company' },
  { name: 'non_profit', value: 'NON_PROFIT', label: 'Non-profit' },
  { name: 'university', value: 'UNIVERSITY', label: 'University' },
  { name: 'other', value: 'OTHER', label: 'Other' },
];

const odkTypeOptions: radioOptionsType[] = [
  { name: 'odk_server_type', value: 'OWN', label: 'Use your own ODK server' },
  { name: 'odk_server_type', value: 'HOT', label: "Request HOT's ODK server" },
];

const CreateEditOrganizationForm = ({ organizationId }: { organizationId: string }) => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const organisationFormData = useAppSelector((state) => state.organisation.organisationFormData);
  const postOrganisationDataLoading = useAppSelector((state) => state.organisation.postOrganisationDataLoading);
  const postOrganisationData = useAppSelector((state) => state.organisation.postOrganisationData);

  useDocumentTitle(organizationId ? 'Manage Organization' : 'Add Organization');

  const submission = () => {
    if (!organizationId) {
      const { ...filteredValues } = values;
      const request_odk_server = filteredValues.odk_server_type === 'HOT';
      dispatch(
        PostOrganisationDataService(`${API_URL}/organisation?request_odk_server=${request_odk_server}`, {
          ...filteredValues,
          logo: filteredValues.logo ? filteredValues.logo?.[0].file : null,
        }),
      );
    } else {
      const { ...filteredValues } = values;
      let changedValues = diffObject(organisationFormData, filteredValues);
      if (changedValues.logo) {
        changedValues = {
          ...changedValues,
          logo: changedValues.logo?.length > 0 ? changedValues.logo?.[0].file : null,
        };
      }
      if (Object.keys(changedValues).length > 0) {
        dispatch(PatchOrganizationDataService(`${API_URL}/organisation/${organizationId}`, changedValues));
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Organization details up to date',
            variant: 'info',
          }),
        );
      }
    }
  };
  const { handleSubmit, handleChange, handleCustomChange, values, errors }: any = useForm(
    organisationFormData,
    submission,
    OrganizationDetailsValidation,
  );

  // redirect to manage-org page after post success
  useEffect(() => {
    if (postOrganisationData) {
      dispatch(OrganisationAction.postOrganisationData(null));
      dispatch(OrganisationAction.SetOrganisationFormData({}));
      dispatch(
        OrganisationAction.SetConsentDetailsFormData({
          give_consent: '',
          review_documentation: [],
          log_into: [],
          participated_in: [],
        }),
      );
      dispatch(OrganisationAction.SetConsentApproval(false));
      if (searchParams.get('popup') === 'true') {
        window.close();
      } else {
        navigate('/organization');
      }
    }
  }, [postOrganisationData]);

  useEffect(() => {
    if (values?.odk_server_type === 'HOT') {
      handleCustomChange('odk_central_url', '');
      handleCustomChange('odk_central_user', '');
      handleCustomChange('odk_central_password', '');
    }
  }, [values?.odk_server_type]);

  return (
    <div className="fmtm-relative fmtm-bg-white fmtm-w-full fmtm-h-full fmtm-flex fmtm-flex-col fmtm-overflow-hidden">
      <div className="fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9 fmtm-flex-1 fmtm-overflow-y-scroll scrollbar">
        {!organizationId && (
          <h5 className="fmtm-text-[#484848] fmtm-text-2xl fmtm-font-[600] fmtm-pb-3 lg:fmtm-pb-7 fmtm-font-archivo fmtm-tracking-wide">
            Organizational Details
          </h5>
        )}
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
          <InputTextField
            id="name"
            name="name"
            label="Community or Organization Name"
            subLabel={!organizationId ? 'Please name the local community or organization you are asking to create' : ''}
            value={values?.name}
            onChange={handleChange}
            fieldType="text"
            required
            errorMsg={errors.name}
          />
          {!organizationId && (
            <InputTextField
              id="url"
              name="url"
              label="Website URL"
              value={values?.url}
              onChange={handleChange}
              fieldType="text"
              required
              errorMsg={errors.url}
            />
          )}
          <InputTextField
            id="associated_email"
            name="associated_email"
            label="Email"
            value={values?.associated_email}
            onChange={handleChange}
            fieldType="text"
            required
            errorMsg={errors.associated_email}
          />
          <TextArea
            id="description"
            name="description"
            label="Description"
            rows={3}
            value={values?.description}
            onChange={handleChange}
            required
            errorMsg={errors.description}
          />
          {!organizationId && (
            <RadioButton
              topic="ODK Server Type"
              options={odkTypeOptions}
              direction="column"
              value={values.odk_server_type}
              onChangeData={(value) => {
                handleCustomChange('odk_server_type', value);
              }}
              className="fmtm-text-base fmtm-text-[#7A7676] fmtm-mt-1"
              errorMsg={errors.odk_server_type}
              required
            />
          )}
          {organizationId && (
            <CustomCheckbox
              label="Update ODK Credentials"
              checked={values?.update_odk_credentials}
              onCheckedChange={(checked) => {
                handleCustomChange('update_odk_credentials', checked);
              }}
            />
          )}
          {(values?.odk_server_type === 'OWN' || values?.update_odk_credentials) && (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
              <InputTextField
                id="odk_central_url"
                name="odk_central_url"
                label="ODK Central URL"
                value={values?.odk_central_url}
                onChange={handleChange}
                fieldType="text"
                errorMsg={errors.odk_central_url}
                required
              />
              <InputTextField
                id="odk_central_user"
                name="odk_central_user"
                label="ODK Central Email"
                value={values?.odk_central_user}
                onChange={handleChange}
                fieldType="text"
                errorMsg={errors.odk_central_user}
                required
              />
              <InputTextField
                id="odk_central_password"
                name="odk_central_password"
                label="ODK Central Password"
                value={values?.odk_central_password}
                onChange={handleChange}
                fieldType="password"
                errorMsg={errors.odk_central_password}
                required
              />
            </div>
          )}
          {!organizationId && (
            <RadioButton
              topic="What type of community or organization are you applying for? "
              options={organizationTypeOptions}
              direction="column"
              value={values.community_type}
              onChangeData={(value) => {
                handleCustomChange('community_type', value);
              }}
              className="fmtm-text-base fmtm-text-[#7A7676] fmtm-mt-1"
              errorMsg={errors.community_type}
              required
            />
          )}
          <UploadArea
            title="Upload Logo"
            label="Please upload .png, .gif, .jpeg"
            data={values?.logo}
            onUploadFile={(updatedFiles) => {
              handleCustomChange('logo', updatedFiles);
            }}
            acceptedInput="image/*"
          />
        </div>
      </div>
      <div className="fmtm-bg-white fmtm-py-2 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-shadow-2xl fmtm-z-50">
        {!organizationId && (
          <Button variant="secondary-red" onClick={() => dispatch(OrganisationAction.SetConsentApproval(false))}>
            Back
          </Button>
        )}

        <Button variant="primary-red" onClick={handleSubmit} isLoading={postOrganisationDataLoading}>
          {!organizationId ? 'Submit' : 'Update'}
        </Button>
      </div>
    </div>
  );
};

export default CreateEditOrganizationForm;
