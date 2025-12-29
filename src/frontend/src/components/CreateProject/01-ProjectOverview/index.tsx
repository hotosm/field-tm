import React, { useEffect, useState } from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { valid } from 'geojson-validation';
import { z } from 'zod/v4';

import { convertFileToGeojson } from '@/utilfunctions/convertFileToGeojson';
import { CommonActions } from '@/store/slices/CommonSlice';
import { createProjectValidationSchema } from '../validation';

import FieldLabel from '@/components/common/FieldLabel';
import { Input } from '@/components/RadixComponents/Input';
import { Textarea } from '@/components/RadixComponents/TextArea';
import { uploadAreaOptions } from '../constants';
import Button from '@/components/common/Button';
import RadioButton from '@/components/common/RadioButton';
import ErrorMessage from '@/components/common/ErrorMessage';
import isEmpty from '@/utilfunctions/isEmpty';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/RadixComponents/Dialog';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import Switch from '@/components/common/Switch';
import FileUpload from '@/components/common/FileUpload';
import { FileType } from '@/types';
import Select2 from '@/components/common/Select2';
import { useGetFormListsQuery } from '@/api/central';
import { TooltipMessage } from '../constants/TooltipMessage';

const ProjectOverview = () => {
  useDocumentTitle('Create Project: Project Overview');

  const dispatch = useAppDispatch();
  const [showLargeAreaWarning, setShowLargeAreaWarning] = useState(false);

  //@ts-ignore
  const authDetails = useAppSelector((state) => state.login.authDetails);
  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, register, control, setValue, formState } = form;
  const { errors } = formState;
  const values = watch();

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

  const { data: formList, isLoading: isGetFormListsLoading } = useGetFormListsQuery({
    options: { queryKey: ['get-form-lists'], staleTime: 60 * 60 * 1000 },
  });
  const sortedFormList =
    formList
      ?.slice()
      .sort((a, b) => a.title.localeCompare(b.title))
      .map((form) => ({ id: form.id, label: form.title, value: form.id })) || [];

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

        {!values.id && (
          <>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Project Area" astric tooltipMessage={<TooltipMessage name="ProjectArea" />} />
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

        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="What are you surveying?" astric />
          <Controller
            control={control}
            name="osm_category"
            render={({ field }) => (
              <Select2
                options={sortedFormList || []}
                value={field.value as string}
                choose="label"
                onChange={(value: any) => {
                  field.onChange(value);
                }}
                placeholder="Form Category"
                isLoading={isGetFormListsLoading}
                ref={field.ref}
              />
            )}
          />
          {errors?.osm_category?.message && <ErrorMessage message={errors.osm_category.message as string} />}
        </div>
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
