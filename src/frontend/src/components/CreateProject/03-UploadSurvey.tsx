import React, { useEffect } from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { Loader2 } from 'lucide-react';
import { Tooltip } from '@mui/material';
import { useAppDispatch } from '@/types/reduxTypes';
import { z } from 'zod/v4';
import { createProjectValidationSchema } from './validation';
import Select2 from '@/components/common/Select2';
import FieldLabel from '@/components/common/FieldLabel';
import ErrorMessage from '@/components/common/ErrorMessage';
import Switch from '@/components/common/Switch';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useDetectFormLanguagesMutation, useGetFormListsQuery } from '@/api/central';
import { CommonActions } from '@/store/slices/CommonSlice';
import FileUpload from '@/components/common/FileUpload';
import isEmpty from '@/utilfunctions/isEmpty';
import { FileType } from '@/types';
import AssetModules from '@/shared/AssetModules';
import { motion } from 'motion/react';
import { useQueryClient } from '@tanstack/react-query';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const prepareRadioOptions = (values: string[]): { label: string; value: string }[] => {
  return values?.map((value) => ({ label: value, value: value }));
};

const UploadSurvey = () => {
  useDocumentTitle('Create Project: Upload Survey');
  const dispatch = useAppDispatch();
  const queryClient = useQueryClient();

  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, control, setValue, formState, clearErrors } = form;
  const { errors } = formState;
  const values = watch();

  const { data: formList, isLoading: isGetFormListsLoading } = useGetFormListsQuery({
    options: { queryKey: ['get-form-lists'], staleTime: 60 * 60 * 1000 },
  });
  const sortedFormList =
    formList
      ?.slice()
      .sort((a, b) => a.title.localeCompare(b.title))
      .map((form) => ({ id: form.id, label: form.title, value: form.id })) || [];

  const { mutate: detectFormLanguagesMutate, isPending: isDetectFormLanguagesPending } = useDetectFormLanguagesMutation(
    {
      onSuccess: ({ data }) => {
        setValue('default_language', '');
        setValue('formLanguages', data);
      },
      onError: ({ response }) => {
        dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Invalid XLSForm form' }));
      },
    },
  );

  const detectDefaultLanguage = (file) => {
    const formData = new FormData();
    formData.append('xlsform', file);
    detectFormLanguagesMutate({
      payload: formData,
    });
  };

  const changeFileHandler = (file: FileType[]): void => {
    if (isEmpty(file)) return;
    setValue('xlsFormFile', file);
    clearErrors();
    setValue('default_language', '');
    values.isFormValidAndUploaded && setValue('isFormValidAndUploaded', false);
    detectDefaultLanguage(file?.[0]?.file);
  };

  const resetFile = (): void => {
    clearErrors();
    setValue('xlsFormFile', []);
    setValue('default_language', '');
    values.isFormValidAndUploaded && setValue('isFormValidAndUploaded', false);
  };

  useEffect(() => {
    if (!values.advancedConfig) {
      let defaultLanguage = '';
      if (!isEmpty(values.formLanguages?.default_language)) {
        defaultLanguage = values.formLanguages?.default_language[0];
      } else if (!isEmpty(values.formLanguages?.detected_languages)) {
        defaultLanguage = values.formLanguages?.detected_languages[0];
      } else {
        defaultLanguage = 'english';
      }
      setValue('default_language', defaultLanguage);
    }
  }, [values.advancedConfig, values.formLanguages]);

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
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
        <FieldLabel className="fmtm-pr-3" label="Include digitization verification questions" />
        <Controller
          control={control}
          name="needVerificationFields"
          render={({ field }) => (
            <Switch
              ref={field.ref}
              checked={field.value}
              onCheckedChange={(e) => {
                field.onChange(e);
                setValue('isFormValidAndUploaded', false);
              }}
              className=""
            />
          )}
        />
      </div>

      <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
        <FieldLabel className="fmtm-pr-20" label="Make photo upload mandatory" />
        <Controller
          control={control}
          name="mandatoryPhotoUpload"
          render={({ field }) => (
            <Switch
              ref={field.ref}
              checked={field.value}
              onCheckedChange={(e) => {
                field.onChange(e);
                setValue('isFormValidAndUploaded', false);
              }}
              className=""
            />
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
        <FileUpload
          placeholder="The supported file formats are .xlsx, .xls, .xml"
          onChange={changeFileHandler}
          onDelete={resetFile}
          data={values.xlsFormFile}
          fileAccept=".xls,.xlsx,.xml"
        />
        {isDetectFormLanguagesPending && (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-primaryRed" />
            <p className="fmtm-text-base">Detecting form languages...</p>
          </div>
        )}
        {!!queryClient.isMutating({ mutationKey: ['upload-project-xlsform'] }) && (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-primaryRed" />
            <p className="fmtm-text-base">Validating & Uploading form...</p>
          </div>
        )}
        {errors?.xlsFormFile?.message && <ErrorMessage message={errors.xlsFormFile.message as string} />}
      </div>
      {!!values.xlsFormFile && isEmpty(values.formLanguages?.default_language) && (
        <>
          <div
            className="fmtm-flex fmtm-items-center fmtm-gap-x-5 fmtm-group fmtm-w-fit fmtm-cursor-pointer"
            onClick={() => {
              setValue('advancedConfig', !values.advancedConfig);
              setValue('default_language', '');
            }}
          >
            <p className="fmtm-button group-hover:fmtm-text-grey-800">Advanced Config</p>
            <motion.div className="" animate={{ rotate: values.advancedConfig ? 180 : 0 }}>
              <AssetModules.ExpandLessIcon className={`!fmtm-text-base group-hover:!fmtm-text-grey-800`} />
            </motion.div>
          </div>
          {values.advancedConfig && (
            <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-flex-wrap">
              <FieldLabel label="Form Default Language" />
              <Controller
                control={control}
                name="default_language"
                render={({ field }) => (
                  <Select2
                    options={
                      !isEmpty(values.formLanguages.detected_languages)
                        ? prepareRadioOptions(values.formLanguages.detected_languages)
                        : prepareRadioOptions(values.formLanguages.supported_languages)
                    }
                    value={field.value as string}
                    choose="label"
                    onChange={(value: any) => {
                      field.onChange(value);
                      setValue('isFormValidAndUploaded', false);
                    }}
                    placeholder="Form Category"
                    isLoading={isGetFormListsLoading}
                    ref={field.ref}
                  />
                )}
              />
              {errors?.default_language?.message && (
                <ErrorMessage message={errors.default_language.message as string} />
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default UploadSurvey;
