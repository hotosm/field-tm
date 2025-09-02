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
import { createProjectValidationSchema, odkCredentialsValidationSchema } from './validation';

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
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/RadixComponents/Dialog';
import { ValidateODKCredentials } from '@/api/CreateProjectService';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import Switch from '@/components/common/Switch';
import { useGetMyOrganisationsQuery, useGetOrganisationsQuery } from '@/api/organisation';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const ProjectOverview = () => {
  useDocumentTitle('Create Project: Project Overview');

  const dispatch = useAppDispatch();
  const isAdmin = useIsAdmin();

  const [userSearchText, setUserSearchText] = useState('');
  const [showODKCredsModal, setShowODKCredsModal] = useState(false);
  const [odkCreds, setOdkCreds] = useState({
    odk_central_url: '',
    odk_central_user: '',
    odk_central_password: '',
  });
  const [odkCredsError, setOdkCredsError] = useState<{
    odk_central_url?: string;
    odk_central_user?: string;
    odk_central_password?: string;
  }>({
    odk_central_url: '',
    odk_central_user: '',
    odk_central_password: '',
  });

  //@ts-ignore
  const authDetails = useAppSelector((state) => state.login.authDetails);
  const userList = useAppSelector((state) => state.user.userListForSelect)?.map((user) => ({
    id: user.sub,
    label: user.username,
    value: user.sub,
  }));
  const userListLoading = useAppSelector((state) => state.user.userListLoading);
  const isODKCredentialsValid = useAppSelector((state) => state.createproject.isODKCredentialsValid);
  const ODKCredentialsValidating = useAppSelector((state) => state.createproject.ODKCredentialsValidating);
  const projectUsersLoading = useAppSelector((state) => state.project.projectUsersLoading);
  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, register, control, setValue, formState } = form;
  const { errors } = formState;
  const values = watch();

  const { data: organisationListData, isLoading: isOrganisationListLoading } = useGetOrganisationsQuery({
    options: { queryKey: ['get-organisation-list'], enabled: isAdmin },
  });

  const { data: myOrganisationListData, isLoading: isMyOrganisationListLoading } = useGetMyOrganisationsQuery({
    options: { queryKey: ['get-my-organisation-list'], enabled: !isAdmin },
  });

  // if draft project created, then instead of calling organisation endpoint populate organisation list with project minimal response data
  const organisationList = values?.id
    ? [
        {
          id: values.organisation_id,
          label: values.organisation_name,
          value: values.organisation_id,
          hasODKCredentials: true,
        },
      ]
    : (isAdmin ? organisationListData : myOrganisationListData)?.map((org) => ({
        id: org.id,
        label: org.name,
        value: org.id,
        hasODKCredentials: !!org?.odk_central_url,
      }));

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
  }, [authDetails, organisationListData, myOrganisationListData]);

  // set odk creds to form state only after validating if the creds are available
  useEffect(() => {
    if (!isODKCredentialsValid) return;
    setValue('odk_central_url', odkCreds.odk_central_url);
    setValue('odk_central_user', odkCreds.odk_central_user);
    setValue('odk_central_password', odkCreds.odk_central_password);

    setShowODKCredsModal(false);
  }, [isODKCredentialsValid]);

  useEffect(() => {
    const outlineArea = values.outlineArea;
    if (values?.id || !outlineArea) return;

    const area = +outlineArea.split(' ')?.[0];
    const unit = outlineArea.split(' ')?.[1];

    if (unit !== 'km²') return;

    if (area > 1000) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'The project area exceeded 1000 Sq.KM. and must be less than 1000 Sq.KM.',
        }),
      );
    } else if (area > 100) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'The project area exceeded over 100 Sq.KM.',
          variant: 'warning',
        }),
      );
    }
  }, [values.outlineArea]);

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
    setValue('outlineArea', undefined);

    if (values.customDataExtractFile) setValue('customDataExtractFile', null);
    if (values.dataExtractGeojson) setValue('dataExtractGeojson', null);
  };

  const validateODKCredentials = async () => {
    const valid = odkCredentialsValidationSchema.safeParse(odkCreds);

    let errors = {};
    if (valid.success) {
      errors = {};
      dispatch(CreateProjectActions.SetODKCredentialsValid(false));
      dispatch(ValidateODKCredentials(`${VITE_API_URL}/helper/odk-credentials-test`, odkCreds));
    } else {
      valid.error.issues.forEach((issue) => {
        errors[issue.path[0]] = issue.message;
      });
    }
    setOdkCredsError(errors);
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
            {values?.short_description?.length}/200
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
              isLoading={isOrganisationListLoading || isMyOrganisationListLoading}
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
            if (!value) setShowODKCredsModal(true);
          }}
          className="fmtm-text-black fmtm-button fmtm-text-sm"
          labelClickable={values.useDefaultODKCredentials}
        />
      )}

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <Dialog
          open={showODKCredsModal}
          onOpenChange={(open) => {
            setShowODKCredsModal(open);
            if (!open)
              setOdkCreds({
                odk_central_url: values.odk_central_url || '',
                odk_central_user: values.odk_central_user || '',
                odk_central_password: values.odk_central_password || '',
              });
          }}
        >
          {values.organisation_id && !values.useDefaultODKCredentials && (
            <DialogTrigger className="fmtm-w-fit">
              <Button variant="primary-red" onClick={() => setShowODKCredsModal(true)}>
                Set ODK Credentials
              </Button>
            </DialogTrigger>
          )}
          <DialogContent>
            <DialogTitle>Set ODK Credentials</DialogTitle>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                <FieldLabel label="ODK Central URL" astric />
                <Input
                  value={odkCreds.odk_central_url}
                  onChange={(e) => setOdkCreds({ ...odkCreds, odk_central_url: e.target.value })}
                />
                {odkCredsError.odk_central_url && <ErrorMessage message={odkCredsError.odk_central_url as string} />}
              </div>
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                <FieldLabel label="ODK Central Email" astric />
                <Input
                  value={odkCreds.odk_central_user}
                  onChange={(e) => setOdkCreds({ ...odkCreds, odk_central_user: e.target.value })}
                />
                {odkCredsError.odk_central_user && <ErrorMessage message={odkCredsError.odk_central_user} />}
              </div>
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                <FieldLabel label="ODK Central Password" astric />
                <Input
                  value={odkCreds.odk_central_password}
                  onChange={(e) => setOdkCreds({ ...odkCreds, odk_central_password: e.target.value })}
                  type="password"
                />
                {odkCredsError.odk_central_password && <ErrorMessage message={odkCredsError.odk_central_password} />}
              </div>
            </div>
            <div className="fmtm-flex fmtm-justify-end fmtm-items-center fmtm-mt-4 fmtm-gap-x-2">
              <Button variant="link-grey" onClick={() => setShowODKCredsModal(false)}>
                Cancel
              </Button>
              <Button variant="primary-red" isLoading={ODKCredentialsValidating} onClick={validateODKCredentials}>
                Confirm
              </Button>
            </div>
          </DialogContent>
        </Dialog>
        {errors?.odk_central_url && errors?.odk_central_user && errors?.odk_central_password && (
          <ErrorMessage message="ODK Credentials are required" />
        )}
      </div>

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="Assign Project Admin" />
        <Controller
          control={control}
          name="project_admins"
          render={({ field }) => (
            <Select2
              name="project_admins"
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
              disabled={projectUsersLoading}
            />
          )}
        />
        {errors?.project_admins?.message && <ErrorMessage message={errors.project_admins.message as string} />}
      </div>

      {!values.id && (
        <>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <FieldLabel
              label="Project Area"
              astric
              tooltipMessage={
                <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
                  <div>
                    <p>Draw:</p>
                    <p>You can draw a freehand polygon on map interface.</p>{' '}
                    <p>Click on the reset button to redraw the AOI.</p>
                  </div>
                  <div>
                    <p>Upload:</p>
                    <p>You may also choose to upload the AOI. Note: The file upload only supports .geojson format. </p>
                  </div>
                  <p>The total area of the AOI is also calculated and displayed on the screen.</p>
                  <p>
                    <b>Note:</b> The uploaded geojson should be in EPSG:4326 coordinate system.
                  </p>
                </div>
              }
            />
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
              <FieldLabel label="Upload AOI" astric />
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
          {values.outlineArea && +values.outlineArea?.split(' ')?.[0] > 1000 && errors?.outlineArea?.message && (
            <ErrorMessage message={errors.outlineArea.message as string} />
          )}

          {values.uploadAreaSelection === 'upload_file' && values.outline && (
            <div className="fmtm-my-2 fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Merge AOI" tooltipMessage="Merge multiple polygons into a single AOI" />
              <Controller
                control={control}
                name="merge"
                render={({ field }) => (
                  <Switch ref={field.ref} checked={field.value} onCheckedChange={field.onChange} className="" />
                )}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ProjectOverview;
