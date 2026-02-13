import React, { useEffect, useRef } from 'react';
import { Controller, useFormContext } from 'react-hook-form';

import { task_split_type } from '@/types/enums';
import { taskSplitOptionsType } from '@/store/types/ICreateProject';
import { useAppDispatch } from '@/types/reduxTypes';
import { createProjectValidationSchema } from './validation';
import { z } from 'zod/v4';

import FieldLabel from '@/components/common/FieldLabel';
import RadioButton from '@/components/common/RadioButton';
import { Input } from '@/components/RadixComponents/Input';
import Button from '@/components/common/Button';
import ErrorMessage from '@/components/common/ErrorMessage';
import AssetModules from '@/shared/AssetModules';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { CommonActions } from '@/store/slices/CommonSlice';
import { usePreviewSplitBySquareMutation, useTaskSplitMutation } from '@/api/project';

const SplitTasks = () => {
  useDocumentTitle('Create Project: Split Tasks');

  const dispatch = useAppDispatch();
  const generateBtnRef = useRef<HTMLButtonElement>(null);

  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, control, register, setValue, formState } = form;
  const { errors } = formState;
  const values = watch();

  const taskSplitOptions: taskSplitOptionsType[] = [
    {
      name: 'define_tasks',
      value: task_split_type.DIVIDE_BY_SQUARE,
      label: 'Divide into square tasks',
      disabled: values.primary_geom_type === 'POLYLINE',
    },
    {
      name: 'define_tasks',
      value: task_split_type.CHOOSE_AREA_AS_TASK,
      label: 'Use uploaded AOI as task areas',
      disabled: false,
    },
    {
      name: 'define_tasks',
      value: task_split_type.TASK_SPLITTING_ALGORITHM,
      label: 'Task Splitting Algorithm',
      disabled: !values.dataExtractGeojson?.features?.length || values.primary_geom_type === 'POLYLINE',
    },
  ];

  const { mutate: previewSplitBySquareMutate, isPending: isPreviewSplitBySquarePending } =
    usePreviewSplitBySquareMutation({
      onSuccess: ({ data }) => {
        setValue('splitGeojsonBySquares', data);
      },
      onError: ({ response }) => {
        dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to upload XLSForm form' }));
      },
    });

  const { mutate: taskSplitMutate, isPending: isTaskSplitPending } = useTaskSplitMutation({
    onSuccess: ({ data }) => {
      setValue('splitGeojsonByAlgorithm', data);
    },
    onError: ({ response }) => {
      dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to upload XLSForm form' }));
    },
  });

  const generateTaskBasedOnSelection = (e) => {
    e.preventDefault();
    e.stopPropagation();

    // Create a file object from the project area Blob
    const projectAreaBlob = new Blob([JSON.stringify(values.outline)], { type: 'application/json' });
    const drawnGeojsonFile = new File([projectAreaBlob], 'outline.json', { type: 'application/json' });

    // Create a file object from the data extract Blob
    const dataExtractBlob = new Blob([JSON.stringify(values.dataExtractGeojson)], { type: 'application/json' });
    const dataExtractFile = new File([dataExtractBlob], 'extract.json', { type: 'application/json' });

    setValue('splitGeojsonBySquares', null);
    setValue('splitGeojsonByAlgorithm', null);

    if (values.task_split_type === task_split_type.DIVIDE_BY_SQUARE) {
      const dividedTaskFormData = new FormData();
      dividedTaskFormData.append('project_geojson', drawnGeojsonFile);
      dividedTaskFormData.append('dimension_meters', values?.task_split_dimension?.toString() || '0');
      previewSplitBySquareMutate({ payload: dividedTaskFormData });
    } else if (values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM) {
      const taskSplittingFileFormData = new FormData();
      taskSplittingFileFormData.append('project_geojson', drawnGeojsonFile);
      taskSplittingFileFormData.append('no_of_buildings', values?.task_num_buildings?.toString() || '0');
      // Only include data extract if custom extract uploaded
      if (dataExtractFile) {
        taskSplittingFileFormData.append('extract_geojson', dataExtractFile);
      }
      taskSplitMutate({
        payload: taskSplittingFileFormData,
      });
    }
  };

  const downloadSplittedGeojson = (geojson) => {
    const blob = new Blob([JSON.stringify(geojson)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'task_splitted_geojson.geojson';
    a.click();
  };

  useEffect(() => {
    if (errors.splitGeojsonBySquares || errors.splitGeojsonByAlgorithm) {
      generateBtnRef?.current?.focus();
    }
  }, [errors.splitGeojsonBySquares, errors.splitGeojsonByAlgorithm]);

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel
          label="Select an option to split your project area"
          astric
          tooltipMessage={
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
              <p>You may choose how to divide an area into tasks for field mapping:</p>
              <p>i) Divide area on squares split the AOI into squares based on user’s input in dimensions</p>
              <p>ii) Choose area as task creates the number of tasks based on number of polygons in AOI</p>
              <p>
                iii) Task splitting algorithm splits an entire AOI into smallers tasks based on linear networks (road,
                river) followed by taking into account the input of number of average buildings per task
              </p>
            </div>
          }
        />
        <Controller
          control={control}
          name="task_split_type"
          render={({ field }) => (
            <RadioButton
              value={field.value || ''}
              options={taskSplitOptions}
              onChangeData={(value) => {
                field.onChange(value);
                if (value === task_split_type.CHOOSE_AREA_AS_TASK && values.splitGeojsonByAlgorithm)
                  setValue('splitGeojsonByAlgorithm', null);
                if (value === task_split_type.CHOOSE_AREA_AS_TASK && values.splitGeojsonBySquares)
                  setValue('splitGeojsonBySquares', null);
              }}
              ref={field.ref}
            />
          )}
        />
        {errors?.task_split_type?.message && <ErrorMessage message={errors.task_split_type.message as string} />}
      </div>

      <div>
        <p className="fmtm-text-gray-500 fmtm-text-sm">
          Total number of features:{' '}
          <span className="fmtm-font-bold">{values.dataExtractGeojson?.features?.length || 0}</span>
        </p>
      </div>

      {values.task_split_type === task_split_type.DIVIDE_BY_SQUARE && (
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <FieldLabel label="Dimension of square in metres:" />
            <Input
              {...register('task_split_dimension', { valueAsNumber: true })}
              className="!fmtm-w-20"
              type="number"
            />
          </div>
          {errors?.task_split_dimension?.message && (
            <ErrorMessage message={errors.task_split_dimension.message as string} />
          )}
        </div>
      )}

      {values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM && (
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <FieldLabel label="Average number of buildings per task:" />
            <Input {...register('task_num_buildings', { valueAsNumber: true })} className="!fmtm-w-20" />
          </div>
          {errors?.task_num_buildings?.message && (
            <ErrorMessage message={errors.task_num_buildings.message as string} />
          )}
        </div>
      )}

      {values.task_split_type &&
        [task_split_type.DIVIDE_BY_SQUARE, task_split_type.TASK_SPLITTING_ALGORITHM].includes(
          values.task_split_type,
        ) && (
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <Button
              ref={generateBtnRef}
              variant="primary-red"
              isLoading={isPreviewSplitBySquarePending || isTaskSplitPending}
              onClick={generateTaskBasedOnSelection}
              disabled={
                (values.task_split_type === task_split_type.DIVIDE_BY_SQUARE && !values.task_split_dimension) ||
                (values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM && !values.task_num_buildings)
                  ? true
                  : false
              }
              shouldFocus
            >
              Click to generate task
              <AssetModules.SettingsIcon />
            </Button>
            {errors?.splitGeojsonBySquares?.message && (
              <ErrorMessage message={errors.splitGeojsonBySquares.message as string} />
            )}
            {errors?.splitGeojsonByAlgorithm?.message && (
              <ErrorMessage message={errors.splitGeojsonByAlgorithm.message as string} />
            )}
          </div>
        )}

      {values.task_split_type && (
        <div>
          <p className="fmtm-text-gray-500 fmtm-text-sm">
            Total number of task:{' '}
            <span className="fmtm-font-bold">
              {values.splitGeojsonByAlgorithm?.features?.length ||
                values.splitGeojsonBySquares?.features?.length ||
                values.outline?.features?.length ||
                values.outline?.coordinates?.length ||
                1}
            </span>
          </p>
          {(values.splitGeojsonByAlgorithm?.features?.length || values.splitGeojsonBySquares?.features?.length) && (
            <Button
              variant="link-grey"
              onClick={() => downloadSplittedGeojson(values.splitGeojsonByAlgorithm || values.splitGeojsonBySquares)}
            >
              <AssetModules.FileDownloadOutlinedIcon />
              Download split geojson
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default SplitTasks;
