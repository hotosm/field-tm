import React, { useEffect } from 'react';
import Button from '@/components/common/Button';
import InputTextField from '@/components/common/InputTextField';
import TextArea from '@/components/common/TextArea';
import { useNavigate } from 'react-router-dom';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import useForm from '@/hooks/useForm';
import OrganizationDetailsValidation from '@/components/CreateEditOrganization/validation/OrganizationDetailsValidation';
import RadioButton from '@/components/common/RadioButton';
import { diffObject } from '@/utilfunctions/compareUtils';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import UploadArea from '@/components/common/UploadArea';
import { CommonActions } from '@/store/slices/CommonSlice';
import { CustomCheckbox } from '@/components/common/Checkbox';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useCreateOrganisationMutation, useUpdateOrganisationMutation } from '@/api/organisation';
import { appendObjectToFormData } from '@/utilfunctions/commonUtils';
import { odkTypeOptions, organizationTypeOptions } from './constants';

const CreateEditOrganizationForm = ({ organizationId }: { organizationId: string }) => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const organisationFormData = useAppSelector((state) => state.organisation.organisationFormData);

  useDocumentTitle(organizationId ? 'Manage Organization' : 'Add Organization');

  const { mutate: createOrganisationMutate, isPending: isOrganisationCreating } = useCreateOrganisationMutation({
    onSuccess: ({ data }) => {
      dispatch(
        CommonActions.SetSnackBar({ message: `${data.name} organization created successfully`, variant: 'success' }),
      );
      navigate('/organization');
    },
    onError: ({ response }) => {
      dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to create organization' }));
    },
  });

  const { mutate: updateOrganisationMutate, isPending: isOrganisationUpdating } = useUpdateOrganisationMutation({
    id: +organizationId,
    options: {
      onSuccess: ({ data }) => {
        dispatch(
          CommonActions.SetSnackBar({ message: `${data.name} organization updated successfully`, variant: 'success' }),
        );
        navigate('/organization');
      },
      onError: ({ response }) => {
        dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to update organization' }));
      },
    },
  });

  const submission = () => {
    if (!organizationId) {
      const request_odk_server = values.odk_server_type === 'HOT';
      const formData = new FormData();
      appendObjectToFormData(formData, {
        ...values,
        logo: values.logo ? values.logo?.[0].file : null,
      });
      createOrganisationMutate({
        payload: formData,
        params: { request_odk_server },
      });
    } else {
      let changedValues = diffObject(organisationFormData, values);
      if (changedValues.logo) {
        changedValues = {
          ...changedValues,
          logo: changedValues.logo?.length > 0 ? changedValues.logo?.[0].file : null,
        };
      }
      if (Object.keys(changedValues).length > 0) {
        updateOrganisationMutate({
          payload: changedValues,
        });
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
        <Button
          variant="primary-red"
          onClick={handleSubmit}
          isLoading={isOrganisationCreating || isOrganisationUpdating}
        >
          {!organizationId ? 'Submit' : 'Update'}
        </Button>
      </div>
    </div>
  );
};

export default CreateEditOrganizationForm;
