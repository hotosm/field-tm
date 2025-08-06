import React, { useEffect } from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { Loader2 } from 'lucide-react';
import { Tooltip } from '@mui/material';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useParams } from 'react-router-dom';
import { FormCategoryService, ValidateCustomForm } from '@/api/CreateProjectService';
import { fileType } from '@/store/types/ICommon';
import { z } from 'zod/v4';
import { createProjectValidationSchema } from './validation';

import Select2 from '@/components/common/Select2';
import FieldLabel from '@/components/common/FieldLabel';
import UploadArea from '@/components/common/UploadArea';
import ErrorMessage from '@/components/common/ErrorMessage';
import Switch from '@/components/common/Switch';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const UploadSurvey = () => {
  useDocumentTitle('Create Project: Upload Survey');

  const dispatch = useAppDispatch();
  const params = useParams();
  const projectId = params.id ? +params.id : null;

  const formExampleList = useAppSelector((state) => state.createproject.formExampleList);
  const formCategoryLoading = useAppSelector((state) => state.createproject.formCategoryLoading);
  const customFileValidity = useAppSelector((state) => state.createproject.customFileValidity);
  const validateCustomFormLoading = useAppSelector((state) => state.createproject.validateCustomFormLoading);
  const sortedFormExampleList = formExampleList
    .slice()
    .sort((a, b) => a.title.localeCompare(b.title))
    .map((form) => ({ id: form.id, label: form.title, value: form.id }));

  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, control, setValue, formState } = form;
  const { errors } = formState;
  const values = watch();

  // fetch all form categories
  useEffect(() => {
    dispatch(FormCategoryService(`${VITE_API_URL}/central/list-forms`));
  }, []);

  const { getValues } = form;
  const uploadXlsformFile = (file) => {
    // use_odk_collect is from previous step, while needVerificationFields is from this step
    const values = getValues();
    const needVerificationFields = values.needVerificationFields;

    dispatch(
      ValidateCustomForm(
        `${VITE_API_URL}/central/upload-xlsform?project_id=${projectId}&use_odk_collect=${values.use_odk_collect}&need_verification_fields=${needVerificationFields}`,
        file?.file,
      ),
    );
  };

  useEffect(() => {
    setValue('isXlsFormFileValid', customFileValidity);
  }, [customFileValidity]);

  const changeFileHandler = (file): void => {
    if (!file) {
      resetFile();
      return;
    }

    setValue('xlsFormFile', file);
    dispatch(CreateProjectActions.SetCustomFileValidity(false));
    uploadXlsformFile(file);
  };

  const resetFile = (): void => {
    setValue('xlsFormFile', null);
    dispatch(CreateProjectActions.SetCustomFileValidity(false));
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="What are you surveying?" astric />
        <Controller
          control={control}
          name="osm_category"
          render={({ field }) => (
            <Select2
              options={sortedFormExampleList || []}
              value={field.value as string}
              choose="label"
              onChange={(value: any) => {
                field.onChange(value);
              }}
              placeholder="Form Category"
              isLoading={formCategoryLoading}
              ref={field.ref}
            />
          )}
        />
        {errors?.osm_category?.message && <ErrorMessage message={errors.osm_category.message as string} />}

        <p className="fmtm-body-sm fmtm-text-[#9B9999]">
          Selecting a form based on OpenStreetMap{' '}
          <a
            href="https://wiki.openstreetmap.org/wiki/Tags"
            target="_"
            className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
          >
            tags
          </a>{' '}
          {`will help with merging the final data back to OSM.`}
        </p>
      </div>

      <div>
        <Tooltip arrow placement="bottom" title={!values.osm_category ? 'Please select a form category first' : ''}>
          <div className="fmtm-w-fit">
            <a
              href={`${VITE_API_URL}/helper/download-template-xlsform?form_type=${values.osm_category}`}
              target="_"
              className={`fmtm-text-sm fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline fmtm-w-fit ${!values.osm_category && 'fmtm-opacity-70 fmtm-pointer-events-none'}`}
            >
              Download Form
            </a>
          </div>
        </Tooltip>
        <p className="fmtm-mt-1">
          <a
            href={`https://xlsform-editor.fmtm.hotosm.org?url=${VITE_API_URL}/helper/download-template-xlsform?form_type=${values.osm_category}`}
            target="_"
            className="fmtm-text-sm fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
          >
            Edit Interactively
          </a>
        </p>
      </div>

      <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
        <FieldLabel label="Include digitization verification questions" />
        <Controller
          control={control}
          name="needVerificationFields"
          render={({ field }) => (
            <Switch ref={field.ref} checked={field.value} onCheckedChange={field.onChange} className="" />
          )}
        />
      </div>

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel
          label="Upload Form"
          astric
          tooltipMessage={
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
              <span>
                You may choose to upload a pre-configured XLSForm, or an entirely custom form. Click{' '}
                <a
                  href="https://hotosm.github.io/osm-fieldwork/about/xlsforms/"
                  target="_"
                  className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer"
                >
                  here
                </a>{' '}
                to learn more about XLSForm building.{' '}
              </span>

              <p>
                <b>Note:</b> Uploading a custom form may make uploading of the final dataset to OSM difficult.
              </p>
              <p>
                <b>Note:</b> Additional questions will be incorporated into your custom form to assess the digitization
                status.
              </p>
            </div>
          }
        />
        <UploadArea
          label="The supported file formats are .xlsx, .xls, .xml"
          data={values.xlsFormFile ? [values.xlsFormFile] : []}
          onUploadFile={(updatedFiles, fileInputRef) => {
            changeFileHandler(updatedFiles?.[0] as fileType);
          }}
          acceptedInput=".xls,.xlsx,.xml"
        />
        {validateCustomFormLoading && (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-primaryRed" />
            <p className="fmtm-text-base">Validating form...</p>
          </div>
        )}
        {errors?.xlsFormFile?.message && <ErrorMessage message={errors.xlsFormFile.message as string} />}
      </div>
    </div>
  );
};

export default UploadSurvey;
