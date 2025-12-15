import React, { useEffect, useState } from 'react';
import { AxiosResponse } from 'axios';
import { zodResolver } from '@hookform/resolvers/zod';
import { editProjectSchema } from './validation';
import { projectType } from '@/types';
import AssetModules from '@/shared/AssetModules';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import Button from '@/components/common/Button';
import RichTextEditor from '@/components/common/Editor/Editor';
import Chips from '@/components/common/Chips';
import RadioButton from '@/components/common/RadioButton';
import { projectStatusOptions, projectVisibilityOptions } from './constants';
import { useForm, Controller } from 'react-hook-form';
import { defaultValues } from './constants/defaultValues';
import FieldLabel from '@/components/common/FieldLabel';
import ErrorMessage from '@/components/common/ErrorMessage';
import { Input } from '@/components/RadixComponents/Input';
import { Textarea } from '@/components/RadixComponents/TextArea';
import { getDirtyFieldValues } from '@/utilfunctions';
import isEmpty from '@/utilfunctions/isEmpty';
import { useAppDispatch } from '@/types/reduxTypes';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useUpdateProjectMutation } from '@/api/project';
import { useQueryClient } from '@tanstack/react-query';

type editDetailsPropsType = {
  project: projectType | undefined;
};

const EditDetails = ({ project }: editDetailsPropsType) => {
  useDocumentTitle('Manage Project: Project Description');
  const dispatch = useAppDispatch();
  const queryClient = useQueryClient();

  const [hashtag, setHashtag] = useState('');

  const formMethods = useForm({
    defaultValues: defaultValues,
    resolver: zodResolver(editProjectSchema),
  });
  const { watch, register, control, setValue, formState, handleSubmit, reset, getValues } = formMethods;
  const { errors, dirtyFields } = formState;
  const values = watch();

  const resetState = (project: projectType) => {
    reset({
      status: project.status,
      name: project.name,
      short_description: project.short_description,
      description: project.description,
      per_task_instructions: project.per_task_instructions,
      hashtags: project.hashtags,
      visibility: project.visibility,
    });
  };

  useEffect(() => {
    if (project) resetState(project);
  }, [project]);

  const { mutate: updateProjectMutate, isPending: isProjectUpdating } = useUpdateProjectMutation({
    id: project?.id!,
    options: {
      onSuccess: ({ data }) => {
        queryClient.setQueryData<AxiosResponse<Record<string, any>>>(['project', data.id], (prevData) => {
          if (!prevData) return prevData;
          return { ...prevData, data };
        });
        dispatch(
          CommonActions.SetSnackBar({
            message: `Project ${data.id} updated successfully`,
            variant: 'success',
          }),
        );
      },
      onError: ({ response }) => {
        dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to update project' }));
      },
    },
  });

  const onSubmit = () => {
    const data = getValues();
    let dirtyValues = getDirtyFieldValues(data, dirtyFields);

    // manually check if hashtags changed
    const isHashtagsChanged = JSON.stringify(control._defaultValues.hashtags) !== JSON.stringify(data.hashtags);
    if (isHashtagsChanged) {
      dirtyValues = {
        ...dirtyValues,
        hashtags: data.hashtags,
      };
    }

    if (isEmpty(dirtyValues)) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'Project details up to date',
          variant: 'info',
        }),
      );
      return;
    }
    updateProjectMutate(dirtyValues);
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="fmtm-relative fmtm-w-full fmtm-h-full fmtm-flex fmtm-flex-col fmtm-overflow-hidden fmtm-bg-white"
    >
      <div className="fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9 fmtm-flex-1 fmtm-overflow-y-scroll scrollbar fmtm-flex fmtm-flex-col fmtm-gap-6">
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="ODK Server Type" astric />
          <Controller
            control={control}
            name="status"
            render={({ field }) => (
              <RadioButton
                value={field.value as string}
                options={projectStatusOptions}
                onChangeData={field.onChange}
                ref={field.ref}
              />
            )}
          />
          {errors?.status?.message && <ErrorMessage message={errors.status.message as string} />}
        </div>

        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="Community or Organization Name" astric />
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
          <FieldLabel label="Instructions" />
          <Controller
            control={control}
            name="per_task_instructions"
            render={({ field }) => (
              <RichTextEditor editorHtmlContent={field.value} setEditorHtmlContent={field.onChange} editable={true} />
            )}
          />
        </div>

        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="Hashtags" />
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

        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="Project Type" astric />
          <Controller
            control={control}
            name="visibility"
            render={({ field }) => (
              <RadioButton value={field.value} options={projectVisibilityOptions} onChangeData={field.onChange} />
            )}
          />
        </div>
      </div>
      <div className="fmtm-py-2 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-shadow-2xl fmtm-z-50">
        <Button variant="primary-red" isLoading={isProjectUpdating} type="submit">
          SAVE
        </Button>
      </div>
    </form>
  );
};

export default EditDetails;
