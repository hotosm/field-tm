import React, { useEffect } from 'react';
import { z } from 'zod/v4';
import { useNavigate, useParams } from 'react-router-dom';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Button from '@/components/common/Button';
import RadioButton from '@/components/common/RadioButton';
import UploadArea from '@/components/common/UploadArea';
import { CustomCheckbox } from '@/components/common/Checkbox';
import FieldLabel from '@/components/common/FieldLabel';
import { Input } from '@/components/RadixComponents/Input';
import ErrorMessage from '@/components/common/ErrorMessage';
import { Textarea } from '@/components/RadixComponents/TextArea';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useAppDispatch } from '@/types/reduxTypes';
import { organisationType } from '@/types';
import { getDirtyFieldValues } from '@/utilfunctions';
import isEmpty from '@/utilfunctions/isEmpty';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useCreateOrganisationMutation, useUpdateOrganisationMutation } from '@/api/organisation';
import { appendObjectToFormData } from '@/utilfunctions/commonUtils';
import { odkTypeOptions, organizationTypeOptions } from './constants';
import { createOrganizationValidationSchema } from './validation/CreateEditOrganization';
import { defaultValues } from './constants/defaultValues';

const CreateEditOrganizationForm = ({ organizationDetail }: { organizationDetail: organisationType | undefined }) => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const params = useParams();

  const orgId = params.id;

  useDocumentTitle(orgId ? 'Manage Organization' : 'Add Organization');

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
    id: +orgId!,
    options: {
      onSuccess: ({ data }) => {
        resetState(data);
        dispatch(
          CommonActions.SetSnackBar({ message: `${data.name} organization updated successfully`, variant: 'success' }),
        );
      },
      onError: ({ response }) => {
        dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to update organization' }));
      },
    },
  });

  const onSubmit = () => {
    if (!orgId) {
      const data = getValues();
      const request_odk_server = data.odk_server_type === 'HOT';
      const formData: FormData & { __type?: z.infer<typeof createOrganizationValidationSchema> } = new FormData();
      appendObjectToFormData(formData, {
        ...data,
        logo: data.logo ? data.logo?.[0].file : null,
      });
      // formData.append('test', 'dsfdsf');
      createOrganisationMutate({
        payload: formData,
        params: { request_odk_server },
      });
    } else {
      const data = getValues();
      const { name, associated_email, description, odk_central_url, logo } = data;
      const dirtyValues = getDirtyFieldValues(
        { name, associated_email, description, odk_central_url, logo },
        dirtyFields,
      );

      if (isEmpty(dirtyValues)) {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Organization details up to date',
            variant: 'info',
          }),
        );
        return;
      }
      const formData = new FormData();
      appendObjectToFormData(formData, {
        ...dirtyValues,
        logo: dirtyValues.logo ? dirtyValues.logo?.[0].file : null,
      });
      updateOrganisationMutate({
        // params: { org_id: +orgId },
        payload: formData,
      });
    }
  };

  const formMethods = useForm<z.infer<typeof createOrganizationValidationSchema>>({
    defaultValues: defaultValues,
    resolver: zodResolver(createOrganizationValidationSchema),
  });
  const { watch, register, control, setValue, formState, handleSubmit, reset, getValues } = formMethods;
  const { errors, dirtyFields } = formState;
  const values = watch();

  const resetState = (organizationDetail: organisationType) => {
    const { name, associated_email, description, odk_central_url, logo, community_type, url } = organizationDetail;
    reset({ ...defaultValues, name, associated_email, description, odk_central_url, logo, community_type, url });
  };

  useEffect(() => {
    if (!organizationDetail || !orgId) return;
    resetState(organizationDetail);
  }, [organizationDetail, orgId]);

  useEffect(() => {
    if (values?.odk_server_type === 'HOT') {
      setValue('odk_central_url', '');
      setValue('odk_central_user', '');
      setValue('odk_central_password', '');
    }
  }, [values?.odk_server_type]);

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="fmtm-relative fmtm-bg-white fmtm-w-full fmtm-h-full fmtm-flex fmtm-flex-col fmtm-overflow-hidden"
    >
      <div className="fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9 fmtm-flex-1 fmtm-overflow-y-scroll scrollbar">
        {!orgId && (
          <h5 className="fmtm-text-[#484848] fmtm-text-2xl fmtm-font-[600] fmtm-pb-3 lg:fmtm-pb-7 fmtm-font-archivo fmtm-tracking-wide">
            Organizational Details
          </h5>
        )}
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="Community or Organization Name" astric />
            <Input {...register('name')} />
            {errors?.name?.message && <ErrorMessage message={errors.name.message as string} />}
          </div>
          {!orgId && (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Website URL" astric />
              <Input {...register('url')} />
              {errors?.url?.message && <ErrorMessage message={errors.url.message as string} />}
            </div>
          )}
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="Email" astric />
            <Input {...register('associated_email')} />
            {errors?.associated_email?.message && <ErrorMessage message={errors.associated_email.message as string} />}
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="Description" astric />
            <Textarea {...register('description')} />
            {errors?.description?.message && <ErrorMessage message={errors.description.message as string} />}
          </div>
          {!orgId && (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="ODK Server Type" astric />
              <Controller
                control={control}
                name="odk_server_type"
                render={({ field }) => (
                  <RadioButton
                    value={field.value as string}
                    options={odkTypeOptions}
                    onChangeData={field.onChange}
                    ref={field.ref}
                  />
                )}
              />
              {errors?.odk_server_type?.message && <ErrorMessage message={errors.odk_server_type.message as string} />}
            </div>
          )}
          {orgId && (
            <CustomCheckbox
              key="update_odk_credentials"
              label="Update ODK Credentials"
              checked={values.update_odk_credentials}
              onCheckedChange={(value) => {
                setValue('update_odk_credentials', value);
              }}
              className="fmtm-text-black fmtm-button fmtm-text-sm"
              labelClickable={values.update_odk_credentials}
            />
          )}
          {(values?.odk_server_type === 'OWN' || values?.update_odk_credentials) && (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                <FieldLabel label="ODK Central URL" astric />
                <Input {...register('odk_central_url')} />
                {errors?.odk_central_url?.message && (
                  <ErrorMessage message={errors.odk_central_url.message as string} />
                )}
              </div>

              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                <FieldLabel label="ODK Central Email" astric />
                <Input {...register('odk_central_user')} />
                {errors?.odk_central_user?.message && (
                  <ErrorMessage message={errors.odk_central_user.message as string} />
                )}
              </div>
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                <FieldLabel label="ODK Central Password" astric />
                <Input {...register('odk_central_password')} />
                {errors?.odk_central_password?.message && (
                  <ErrorMessage message={errors.odk_central_password.message as string} />
                )}
              </div>
            </div>
          )}
          {!orgId && (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="What type of community or organization are you applying for?" astric />
              <Controller
                control={control}
                name="community_type"
                render={({ field }) => (
                  <RadioButton
                    value={field.value as string}
                    options={organizationTypeOptions}
                    onChangeData={field.onChange}
                    ref={field.ref}
                  />
                )}
              />
            </div>
          )}
          <div className="fmtm-my-2 fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="Upload Logo" />
            <UploadArea
              title=""
              label="Please upload .png, .gif, .jpeg"
              data={values.logo}
              onUploadFile={(updatedFiles, fileInputRef) => {
                setValue('logo', updatedFiles?.[0]);
              }}
              acceptedInput="image/*"
            />
            {errors?.logo?.message && <ErrorMessage message={errors.logo.message as string} />}
          </div>
        </div>
      </div>
      <div className="fmtm-bg-white fmtm-py-2 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-shadow-2xl fmtm-z-50">
        {!orgId && (
          <Button variant="secondary-red" onClick={() => dispatch(OrganisationAction.SetConsentApproval(false))}>
            Back
          </Button>
        )}
        <Button type="submit" variant="primary-red" isLoading={isOrganisationCreating || isOrganisationUpdating}>
          {!orgId ? 'Submit' : 'Update'}
        </Button>
      </div>
    </form>
  );
};

export default CreateEditOrganizationForm;
