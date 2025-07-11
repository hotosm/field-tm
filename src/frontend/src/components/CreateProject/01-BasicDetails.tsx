import React, { useEffect, useState } from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { valid } from 'geojson-validation';
import { useIsAdmin } from '@/hooks/usePermissions';
import { z } from 'zod/v4';

import { GetUserListForSelect } from '@/api/User';
import { UserActions } from '@/store/slices/UserSlice';
import { convertFileToGeojson } from '@/utilfunctions/convertFileToGeojson';
import { fileType } from '@/store/types/ICommon';
import { CommonActions } from '@/store/slices/CommonSlice';
import { createProjectValidationSchema } from './validation';

import { CustomCheckbox } from '@/components/common/Checkbox';
import FieldLabel from '@/components/common/FieldLabel';
import { Input } from '@/components/RadixComponents/Input';
import Select2 from '@/components/common/Select2';
import { Textarea } from '@/components/RadixComponents/TextArea';
import { uploadAreaOptions } from './constants';
import Button from '@/components/common/Button';
import RadioButton from '@/components/common/RadioButton';
import UploadAreaComponent from '@/components/common/UploadArea';
import ErrorMessage from '@/components/common/ErrorMessage';
import isEmpty from '@/utilfunctions/isEmpty';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const BasicDetails = () => {
  const dispatch = useAppDispatch();
  const isAdmin = useIsAdmin();

  const [userSearchText, setUserSearchText] = useState('');

  //@ts-ignore
  const authDetails = useAppSelector((state) => state.login.authDetails);
  const organisationListData = useAppSelector((state) => state.createproject.organisationList);
  const organisationListLoading = useAppSelector((state) => state.createproject.organisationListLoading);
  const userList = useAppSelector((state) => state.user.userListForSelect)?.map((user) => ({
    id: user.sub,
    label: user.username,
    value: user.sub,
  }));
  const userListLoading = useAppSelector((state) => state.user.userListLoading);

  const organisationList = organisationListData.map((org) => ({
    id: org.id,
    label: org.name,
    value: org.id,
    hasODKCredentials: !!org?.odk_central_url,
  }));

  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, register, control, setValue, formState } = form;
  const { errors } = formState;

  const values = watch();

  useEffect(() => {
    if (!userSearchText) return;
    dispatch(
      GetUserListForSelect(`${VITE_API_URL}/users/usernames`, {
        search: userSearchText,
        signin_type: 'osm',
      }),
    );
  }, [userSearchText]);

  useEffect(() => {
    if (!authDetails || isEmpty(organisationList) || isAdmin || authDetails?.orgs_managed?.length > 1 || !!values.id)
      return;

    setValue('organisation_id', authDetails?.orgs_managed[0]);
    handleOrganizationChange(authDetails?.orgs_managed[0]);
  }, [authDetails, organisationListData]);

  const handleOrganizationChange = (orgId: number) => {
    const orgIdInt = orgId && +orgId;
    if (!orgIdInt) return;
    const selectedOrg = organisationList.find((org) => org.value === orgIdInt);
    setValue('hasODKCredentials', !!selectedOrg?.hasODKCredentials);
    setValue('useDefaultODKCredentials', !!selectedOrg?.hasODKCredentials);
  };

  const changeFileHandler = async (file: fileType, fileInputRef: React.RefObject<HTMLInputElement | null>) => {
    if (!file) {
      resetFile();
      return;
    }

    const fileObject = file?.file;
    const convertedGeojson = await convertFileToGeojson(fileObject);
    const isGeojsonValid = valid(convertedGeojson, true);

    if (isGeojsonValid?.length === 0) {
      setValue('uploadedAOIFile', file);
      setValue('outline', convertedGeojson);
    } else {
      setValue('uploadedAOIFile', null);
      setValue('outline', null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      dispatch(
        CommonActions.SetSnackBar({
          message: `The uploaded GeoJSON is invalid and contains the following errors: ${isGeojsonValid?.map((error) => `\n${error}`)}`,
          duration: 10000,
        }),
      );
    }
  };

  const resetFile = () => {
    setValue('uploadedAOIFile', null);
    setValue('outline', null);

    if (values.customDataExtractFile) setValue('customDataExtractFile', null);
    if (values.dataExtractGeojson) setValue('dataExtractGeojson', null);
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="Project Name" astric />
        <Input {...register('name')} />
        {errors?.name?.message && <ErrorMessage message={errors.name.message as string} />}
      </div>

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="Short Description" astric />
        <div className="relative">
          <Textarea {...register('short_description')} maxLength={200} />
          <p className="fmtm-text-xs fmtm-absolute fmtm-bottom-1 fmtm-right-2 fmtm-text-gray-400">
            {values.short_description.length}/200
          </p>
        </div>
        {errors?.short_description?.message && <ErrorMessage message={errors.short_description.message as string} />}
      </div>

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="Description" astric />
        <Textarea {...register('description')} />
        {errors?.description?.message && <ErrorMessage message={errors.description.message as string} />}
      </div>

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        {/* preselect organization if user org-admin & manages only one org */}
        <FieldLabel label="Organization Name" astric />
        <Controller
          control={control}
          name="organisation_id"
          render={({ field }) => (
            <Select2
              options={organisationList || []}
              value={field.value as number}
              onChange={(value: any) => {
                field.onChange(value);
                handleOrganizationChange(value);
              }}
              placeholder="Organization Name"
              disabled={(!isAdmin && authDetails?.orgs_managed?.length === 1) || !!values.id}
              isLoading={organisationListLoading}
              ref={field.ref}
            />
          )}
        />
        {errors?.organisation_id?.message && <ErrorMessage message={errors.organisation_id.message as string} />}
      </div>

      {values.organisation_id && values.hasODKCredentials && !values.id && (
        <CustomCheckbox
          key="useDefaultODKCredentials"
          label="Use default or requested ODK credentials"
          checked={values.useDefaultODKCredentials}
          onCheckedChange={(value) => {
            setValue('useDefaultODKCredentials', value);
          }}
          className="fmtm-text-black fmtm-button fmtm-text-sm"
          labelClickable={values.useDefaultODKCredentials}
        />
      )}

      {values.organisation_id && !values.useDefaultODKCredentials && !values.id && (
        <>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="ODK Central URL" astric />
            <Input {...register('odk_central_url')} />
            {errors?.odk_central_url?.message && <ErrorMessage message={errors.odk_central_url.message as string} />}
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="ODK Central Email" astric />
            <Input {...register('odk_central_user')} />
            {errors?.odk_central_user?.message && <ErrorMessage message={errors.odk_central_user.message as string} />}
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="ODK Central Password" astric />
            <Input {...register('odk_central_password')} />
            {errors?.odk_central_password?.message && (
              <ErrorMessage message={errors.odk_central_password.message as string} />
            )}
          </div>
        </>
      )}

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="Assign Project Admin" />
        <Controller
          control={control}
          name="project_admins"
          render={({ field }) => (
            <Select2
              options={userList || []}
              value={field.value}
              onChange={(value: any) => field.onChange(value)}
              placeholder="Search for Field-TM users"
              multiple
              checkBox
              isLoading={userListLoading}
              handleApiSearch={(value) => {
                if (value) {
                  setUserSearchText(value);
                } else {
                  dispatch(UserActions.SetUserListForSelect([]));
                }
              }}
              ref={field.ref}
            />
          )}
        />
        {errors?.project_admins?.message && <ErrorMessage message={errors.project_admins.message as string} />}
      </div>

      {!values.id && (
        <>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel label="Project Area" astric />
            <Controller
              control={control}
              name="uploadAreaSelection"
              render={({ field }) => (
                <RadioButton
                  value={field.value as string}
                  options={uploadAreaOptions}
                  onChangeData={field.onChange}
                  ref={field.ref}
                />
              )}
            />
            {errors?.uploadAreaSelection?.message && (
              <ErrorMessage message={errors.uploadAreaSelection.message as string} />
            )}
          </div>
          {values.uploadAreaSelection === 'draw' && (
            <div>
              <p className="fmtm-text-gray-700 fmtm-pb-2 fmtm-text-sm">Draw a polygon on the map to plot the area</p>
              {errors?.outline?.message && <ErrorMessage message={errors.outline.message as string} />}
              {values.outline && (
                <>
                  <Button variant="secondary-grey" onClick={() => resetFile()}>
                    Reset
                  </Button>
                  <p className="fmtm-text-gray-700 fmtm-mt-2 fmtm-text-xs">
                    Total Area: <span className="fmtm-font-bold">{values.outlineArea}</span>
                  </p>
                </>
              )}
            </div>
          )}
          {values.uploadAreaSelection === 'upload_file' && (
            <div className="fmtm-my-2 fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Select one of the option to upload area" astric />
              <UploadAreaComponent
                title=""
                label="Please upload .geojson, .json file"
                data={values.uploadedAOIFile ? [values.uploadedAOIFile] : []}
                onUploadFile={(updatedFiles, fileInputRef) => {
                  changeFileHandler(updatedFiles?.[0] as fileType, fileInputRef);
                }}
                acceptedInput=".geojson, .json"
              />
              {errors?.uploadedAOIFile?.message && <ErrorMessage message={errors.uploadedAOIFile.message as string} />}
              {values.outline && (
                <p className="fmtm-text-gray-700 fmtm-mt-2 fmtm-text-xs">
                  Total Area: <span className="fmtm-font-bold">{values.outlineArea}</span>
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BasicDetails;
