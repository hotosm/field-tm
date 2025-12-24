import React, { useEffect, useState } from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { valid } from 'geojson-validation';
import { useIsAdmin } from '@/hooks/usePermissions';
import { z } from 'zod/v4';

import { convertFileToGeojson } from '@/utilfunctions/convertFileToGeojson';
import { CommonActions } from '@/store/slices/CommonSlice';
import { createProjectValidationSchema, odkCredentialsValidationSchema } from './validation';

import FieldLabel from '@/components/common/FieldLabel';
import { Input } from '@/components/RadixComponents/Input';
import { Textarea } from '@/components/RadixComponents/TextArea';
import { uploadAreaOptions } from './constants';
import Button from '@/components/common/Button';
import RadioButton from '@/components/common/RadioButton';
import ErrorMessage from '@/components/common/ErrorMessage';
import isEmpty from '@/utilfunctions/isEmpty';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/RadixComponents/Dialog';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import Switch from '@/components/common/Switch';
import { useGetUserListQuery } from '@/api/user';
import { useTestOdkCredentialsMutation } from '@/api/central';
import { field_mapping_app } from '@/types/enums';
import { useTestQFieldCredentialsMutation } from '@/api/qfield';
import FileUpload from '@/components/common/FileUpload';
import { FileType } from '@/types';

const MAPPING_APP_LABELS: Record<field_mapping_app, string> = {
  ODK: 'ODK Central',
  FieldTM: 'ODK Central',
  QField: 'QField Coud',
};

const ProjectOverview = () => {
  useDocumentTitle('Create Project: Project Overview');

  const dispatch = useAppDispatch();
  const isAdmin = useIsAdmin();

  const [userSearchText, setUserSearchText] = useState('');
  const [showODKCredsModal, setShowODKCredsModal] = useState(false);
  const [showLargeAreaWarning, setShowLargeAreaWarning] = useState(false);
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
  const projectUsersLoading = useAppSelector((state) => state.project.projectUsersLoading);
  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, register, control, setValue, formState } = form;
  const { errors } = formState;
  const values = watch();

  const { data: users, isLoading: userListLoading } = useGetUserListQuery({
    params: { search: userSearchText, signin_type: 'osm' },
    options: {
      queryKey: ['get-user-list', userSearchText],
      enabled: !!userSearchText,
      staleTime: 60 * 60 * 1000,
    },
  });
  const userList =
    users?.map((user) => ({
      id: user.sub,
      label: user.username,
      value: user.sub,
    })) || [];

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
          duration: 10000,
        }),
      );
    } else if (area > 100) {
      dispatch(
        CommonActions.SetSnackBar({
          duration: 10000,
          message: 'The project area exceeded over 100 Sq.KM.',
          variant: 'warning',
        }),
      );
    }
  }, [values.outlineArea]);

  useEffect(() => {
    if (errors.proceedWithLargeOutlineArea) setShowLargeAreaWarning(true);
  }, [errors.proceedWithLargeOutlineArea]);

  const changeFileHandler = async (file: FileType[]) => {
    if (isEmpty(file)) return;

    const fileObject = file?.[0]?.file;
    const convertedGeojson = await convertFileToGeojson(fileObject);
    const isGeojsonValid = valid(convertedGeojson, true);

    if (isGeojsonValid?.length === 0) {
      setValue('uploadedAOIFile', file);
      setValue('outline', convertedGeojson);
    } else {
      setValue('uploadedAOIFile', []);
      setValue('outline', null);
      dispatch(
        CommonActions.SetSnackBar({
          message: `The uploaded GeoJSON is invalid and contains the following errors: ${isGeojsonValid?.map((error) => `\n${error}`)}`,
          duration: 10000,
        }),
      );
    }
  };

  const resetFile = () => {
    setValue('uploadedAOIFile', []);
    setValue('outline', null);
    setValue('outlineArea', undefined);

    if (values.customDataExtractFile) setValue('customDataExtractFile', []);
    if (values.dataExtractGeojson) setValue('dataExtractGeojson', null);
  };

  const saveServerCredentials = () => {
    setValue('odk_central_url', odkCreds.odk_central_url);
    setValue('odk_central_user', odkCreds.odk_central_user);
    setValue('odk_central_password', odkCreds.odk_central_password);
    setShowODKCredsModal(false);
  };

  const { mutate: validateODKCredentialsMutate, isPending: isODKCredentialsValidating } = useTestOdkCredentialsMutation(
    {
      onSuccess: saveServerCredentials,
      onError: ({ response }) => {
        dispatch(
          CommonActions.SetSnackBar({ message: response?.data?.detail || 'Failed to validate ODK credentials' }),
        );
      },
    },
  );

  const { mutate: validateQFieldCredentialsMutate, isPending: isQFieldCredentialsValidating } =
    useTestQFieldCredentialsMutation({
      onSuccess: saveServerCredentials,
      onError: ({ response }) => {
        dispatch(
          CommonActions.SetSnackBar({ message: response?.data?.detail || 'Failed to validate QField credentials' }),
        );
      },
    });

  const validateODKCredentials = async () => {
    const valid = odkCredentialsValidationSchema.safeParse({
      field_mapping_app: values.field_mapping_app,
      ...odkCreds,
    });

    let errors = {};
    if (valid.success) {
      errors = {};
      if (values.field_mapping_app === field_mapping_app.QField) {
        validateQFieldCredentialsMutate({ params: odkCreds });
      } else {
        validateODKCredentialsMutate({ params: odkCreds });
      }
    } else {
      valid.error.issues.forEach((issue) => {
        errors[issue.path[0]] = issue.message;
      });
    }
    setOdkCredsError(errors);
  };

  return (
    <>
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="Project Name" astric />
          <Input {...register('project_name')} />
          {errors?.project_name?.message && <ErrorMessage message={errors.project_name.message as string} />}
        </div>

        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="Description" astric />
          <Textarea {...register('description')} />
          {errors?.description?.message && <ErrorMessage message={errors.description.message as string} />}
        </div>

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
            <DialogTrigger className="fmtm-w-fit">
              <Button variant="primary-red" onClick={() => setShowODKCredsModal(true)}>
                Set {MAPPING_APP_LABELS[values.field_mapping_app!]} Credentials
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogTitle>Set {MAPPING_APP_LABELS[values.field_mapping_app!]} Credentials</DialogTitle>
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
                <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                  <FieldLabel label={`${MAPPING_APP_LABELS[values.field_mapping_app!]} URL`} astric />
                  <Input
                    value={odkCreds.odk_central_url}
                    onChange={(e) => setOdkCreds({ ...odkCreds, odk_central_url: e.target.value })}
                  />
                  {odkCredsError.odk_central_url && <ErrorMessage message={odkCredsError.odk_central_url as string} />}
                </div>
                <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                  <FieldLabel label={`${MAPPING_APP_LABELS[values.field_mapping_app!]} Email`} astric />
                  <Input
                    value={odkCreds.odk_central_user}
                    onChange={(e) => setOdkCreds({ ...odkCreds, odk_central_user: e.target.value })}
                  />
                  {odkCredsError.odk_central_user && <ErrorMessage message={odkCredsError.odk_central_user} />}
                </div>
                <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                  <FieldLabel label={`${MAPPING_APP_LABELS[values.field_mapping_app!]} Password`} astric />
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
                <Button
                  variant="primary-red"
                  isLoading={isODKCredentialsValidating || isQFieldCredentialsValidating}
                  onClick={validateODKCredentials}
                >
                  Confirm
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          {errors?.odk_central_url && errors?.odk_central_user && errors?.odk_central_password && (
            <ErrorMessage message="ODK Credentials are required" />
          )}
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
                      <p>
                        You may also choose to upload the AOI. Note: The file upload only supports .geojson format.{' '}
                      </p>
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
                <FileUpload
                  onChange={changeFileHandler}
                  onDelete={resetFile}
                  data={values.uploadedAOIFile}
                  fileAccept=".geojson, .json"
                  placeholder="Please upload .geojson, .json file"
                />
                {errors?.uploadedAOIFile?.message && (
                  <ErrorMessage message={errors.uploadedAOIFile.message as string} />
                )}
                {values.outline && (
                  <p className="fmtm-text-gray-700 fmtm-mt-2 fmtm-text-xs">
                    Total Area: <span className="fmtm-font-bold">{values.outlineArea}</span>
                  </p>
                )}
              </div>
            )}
            {values.outlineArea &&
              +values.outlineArea?.split(' ')?.[0] > 1000 &&
              values.outlineArea?.split(' ')[1] === 'km²' &&
              errors?.outlineArea?.message && <ErrorMessage message={errors.outlineArea.message as string} />}

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
      <Dialog open={showLargeAreaWarning} onOpenChange={(status) => setShowLargeAreaWarning(status)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Mapping area exceeds 200km²</DialogTitle>
          </DialogHeader>
          <div>
            <p className="fmtm-mb-2">
              The mapping area is very large <b>&gt;200km²</b>. Could you consider subdividing into smaller projects?
            </p>
            <p>
              <b>Note:</b> Getting data from OSM will not work for areas <b>&gt;200km²</b>, so you will have to provide
              your own data.
            </p>
            <div className="fmtm-flex fmtm-justify-end fmtm-items-center fmtm-mt-4 fmtm-gap-x-2">
              <Button
                variant="link-grey"
                onClick={() => {
                  setShowLargeAreaWarning(false);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary-red"
                onClick={() => {
                  setValue('proceedWithLargeOutlineArea', true);
                  setShowLargeAreaWarning(false);
                }}
              >
                Confirm
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ProjectOverview;
