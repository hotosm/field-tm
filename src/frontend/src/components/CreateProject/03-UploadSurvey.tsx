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
      </div>
      <div className="fmtm-body-md fmtm-inline">
        We have some sample forms for the type of survey category you chose above. You can{' '}
        <Tooltip arrow placement="bottom" title={!values.osm_category ? 'Please select a form category first' : ''}>
          <span className="fmtm-inline-block">
            <a
              href={`${VITE_API_URL}/helper/download-template-xlsform?form_type=${values.osm_category}`}
              target="_"
              className={`fmtm-text-sm fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline fmtm-w-fit ${!values.osm_category && 'fmtm-opacity-70 fmtm-pointer-events-none'}`}
            >
              download form
            </a>
          </span>
        </Tooltip>{' '}
        and modify in your device or{' '}
        <a
          href={`https://xlsform-editor.fmtm.hotosm.org?url=${VITE_API_URL}/helper/download-template-xlsform?form_type=${values.osm_category}`}
          target="_"
          className="fmtm-text-sm fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
        >
          edit interactively
        </a>{' '}
        from the browser.
      </div>
      <div className="fmtm-border fmtm-border-yellow-400 fmtm-rounded-xl fmtm-bg-yellow-50 fmtm-py-3 fmtm-px-5">
        <div className="fmtm-flex fmtm-gap-2 fmtm-items-center fmtm-mb-1">
          <AssetModules.WarningIcon className=" fmtm-text-yellow-500" sx={{ fontSize: '20px' }} />
          <h5 className="fmtm-text-[1rem] fmtm-font-semibold">Warning</h5>
        </div>
        <div>
          <p className="fmtm-body-md">
            We add a few additional questions into your form to assess the digitization status. View additional fields{' '}
            <a
              href="https://docs.fieldtm.hotosm.org/manuals/xlsform-design/#injected-fields-in-the-field-tm-xls-form"
              target="_"
              className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
            >
              here
            </a>
            . If you don&apos;t wish to include those, kindly toggle this button
          </p>
        </div>
        <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mt-4">
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
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem]">
            <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
              <FieldLabel
                className="fmtm-pr-20"
                label="Make photo upload mandatory"
                tooltipMessage="Make photo upload mandatory when submitting the form."
              />
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
            {!isEmpty(values.xlsFormFile) && isEmpty(values.formLanguages?.default_language) && (
              <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-flex-wrap">
                <FieldLabel
                  label="Select Default Form Language"
                  tooltipMessage="Your form includes multiple languages, but no default is set. Please choose a default language."
                />
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
          </div>
        )}
      </>
    </div>
  );
};

export default UploadSurvey;
