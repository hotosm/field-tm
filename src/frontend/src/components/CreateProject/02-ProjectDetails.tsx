import React, { useEffect, useState } from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { z } from 'zod/v4';
import { createProjectValidationSchema } from './validation';

import { useAppSelector } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import { projectVisibilityOptions } from './constants';
import FieldLabel from '@/components/common/FieldLabel';
import RadioButton from '@/components/common/RadioButton';
import Button from '@/components/common/Button';
import Chips from '@/components/common/Chips';
import { Input } from '@/components/RadixComponents/Input';
import Switch from '@/components/common/Switch';
import RichTextEditor from '@/components/common/Editor/Editor';
import ErrorMessage from '@/components/common/ErrorMessage';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const ProjectDetails = () => {
  useDocumentTitle('Create Project: Project Details');

  const { hostname } = window.location;
  const [hashtag, setHashtag] = useState('');

  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, register, control, setValue, formState } = form;
  const { errors } = formState;

  const values = watch();
  const fieldMappingApp = useAppSelector((state) => state.createproject.fieldMappingApp);

  useEffect(() => {
    if (!values.hasCustomTMS && values.custom_tms_url) setValue('custom_tms_url', '');
  }, [values.hasCustomTMS]);

  useEffect(() => {
    console.log(fieldMappingApp);
    if (!fieldMappingApp) {
      setValue('use_odk_collect', false);
    } else {
      // Set use_odk_collect only if app type is ODK
      setValue('use_odk_collect', fieldMappingApp === 'ODK');
    }
  }, [fieldMappingApp, setValue]);

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel
          label="Project Type"
          astric
          tooltipMessage={
            <span>
              You can choose the visibility of your project. A{' '}
              <span className="fmtm-font-semibold">public project</span> is accessible to everyone, while a{' '}
              <span className="fmtm-font-semibold">private project</span> is only accessible to invited users and
              admins.
            </span>
          }
        />
        <Controller
          control={control}
          name="visibility"
          render={({ field }) => (
            <RadioButton value={field.value} options={projectVisibilityOptions} onChangeData={field.onChange} />
          )}
        />
      </div>

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel
          label="Hashtags"
          tooltipMessage={`Hashtags relate to what is being mapped. By default ${['#Field-TM', `#${hostname}-${values.id}`]} is included. Hashtags are sometimes
          used for analysis later, but should be human informative and not overused, #group #event`}
        />
        <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
          <Input value={hashtag} onChange={(e) => setHashtag(e.target.value)} className="fmtm-flex-1" />
          <Button
            disabled={!hashtag.trim()}
            variant="primary-red"
            className="!fmtm-rounded-full !fmtm-w-5 !fmtm-h-5 fmtm-mb-[2px] !fmtm-p-0"
            onClick={() => {
              if (!hashtag.trim()) return;
              setValue('hashtags', [...values.hashtags, hashtag]);
              setHashtag('');
            }}
          >
            <AssetModules.AddIcon className="!fmtm-text-lg" />
          </Button>
        </div>
        <div>
          <Chips
            className="fmtm-my-2 fmtm-flex-wrap"
            data={values.hashtags}
            clearChip={(i) =>
              setValue(
                'hashtags',
                values.hashtags.filter((_, index) => index !== i),
              )
            }
          />
        </div>
      </div>

      <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
        <FieldLabel
          label="Use a custom TMS basemap"
          tooltipMessage={
            <span>
              You can use the &apos; Custom TMS URL&apos; option to integrate high-resolution aerial imagery like
              OpenAerialMap{' '}
              <a
                href="https://openaerialmap.org/"
                className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
                target="_"
              >
                (OAM)
              </a>
              . Simply obtain the TMS URL and paste it into the custom TMS field. More details:{' '}
              <a
                href="https://docs.openaerialmap.org/"
                className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
                target="_"
              >
                OpenAerialMap Documentation
              </a>
              .
            </span>
          }
        />
        <Controller
          control={control}
          name="hasCustomTMS"
          render={({ field }) => (
            <Switch ref={field.ref} checked={field.value} onCheckedChange={field.onChange} className="" />
          )}
        />
      </div>

      {values.hasCustomTMS && (
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="TMS URL" astric />
          <Input {...register('custom_tms_url')} />
          {errors?.custom_tms_url?.message && <ErrorMessage message={errors.custom_tms_url.message as string} />}
        </div>
      )}

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="Instructions" />
        <Controller
          control={control}
          name="per_task_instructions"
          render={({ field }) => (
            <RichTextEditor editorHtmlContent={field.value} setEditorHtmlContent={field.onChange} editable={true} />
          )}
        />
      </div>
    </div>
  );
};

export default ProjectDetails;
