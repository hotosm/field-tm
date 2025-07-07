import React, { useEffect, useRef } from 'react';
import { Controller, useFormContext } from 'react-hook-form';

import { task_split_type } from '@/types/enums';
import { taskSplitOptionsType } from '@/store/types/ICreateProject';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { GetDividedTaskFromGeojson, TaskSplittingPreviewService } from '@/api/CreateProjectService';
import { createProjectValidationSchema } from './validation';
import { z } from 'zod/v4';

import FieldLabel from '@/components/common/FieldLabel';
import RadioButton from '@/components/common/RadioButton';
import { Input } from '@/components/RadixComponents/Input';
import Button from '@/components/common/Button';
import ErrorMessage from '@/components/common/ErrorMessage';
import AssetModules from '@/shared/AssetModules';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const SplitTasks = () => {
  const dispatch = useAppDispatch();
  const generateBtnRef = useRef<HTMLButtonElement>(null);

  const splitGeojsonBySquares = useAppSelector((state) => state.createproject.splitGeojsonBySquares);
  const splitGeojsonByAlgorithm = useAppSelector((state) => state.createproject.splitGeojsonByAlgorithm);
  const dividedTaskLoading = useAppSelector((state) => state.createproject.dividedTaskLoading);
  const taskSplittingGeojsonLoading = useAppSelector((state) => state.createproject.taskSplittingGeojsonLoading);

  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, control, register, setValue, formState } = form;
  const { errors } = formState;
  const values = watch();

  const taskSplitOptions: taskSplitOptionsType[] = [
    {
      name: 'define_tasks',
      value: task_split_type.DIVIDE_ON_SQUARE,
      label: 'Divide into square tasks',
      disabled: false,
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
      disabled: !values.dataExtractGeojson?.features?.length || values.primaryGeomType === 'POLYLINE',
    },
  ];

  const generateTaskBasedOnSelection = (e) => {
    e.preventDefault();
    e.stopPropagation();

    // Create a file object from the project area Blob
    const projectAreaBlob = new Blob([JSON.stringify(values.outline)], { type: 'application/json' });
    const drawnGeojsonFile = new File([projectAreaBlob], 'outline.json', { type: 'application/json' });

    // Create a file object from the data extract Blob
    const dataExtractBlob = new Blob([JSON.stringify(values.dataExtractGeojson)], { type: 'application/json' });
    const dataExtractFile = new File([dataExtractBlob], 'extract.json', { type: 'application/json' });

    if (values.task_split_type === task_split_type.DIVIDE_ON_SQUARE) {
      dispatch(
        GetDividedTaskFromGeojson(`${VITE_API_URL}/projects/preview-split-by-square`, {
          geojson: drawnGeojsonFile,
          extract_geojson: values.dataExtractType === 'osm_data_extract' ? null : dataExtractFile,
          dimension: values?.dimension,
        }),
      );
    } else if (values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM) {
      dispatch(
        TaskSplittingPreviewService(
          `${VITE_API_URL}/projects/task-split`,
          drawnGeojsonFile,
          values?.average_buildings_per_task as number,
          values.dataExtractType === 'osm_data_extract' ? null : dataExtractFile,
        ),
      );
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
    setValue('splitGeojsonBySquares', splitGeojsonBySquares);
  }, [splitGeojsonBySquares]);

  useEffect(() => {
    setValue('splitGeojsonByAlgorithm', splitGeojsonByAlgorithm);
  }, [splitGeojsonByAlgorithm]);

  useEffect(() => {
    if (errors.splitGeojsonBySquares || errors.splitGeojsonByAlgorithm) {
      generateBtnRef?.current?.focus();
    }
  }, [errors.splitGeojsonBySquares, errors.splitGeojsonByAlgorithm]);

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel label="Select an option to split your project area" astric />
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

      {values.task_split_type === task_split_type.DIVIDE_ON_SQUARE && (
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <FieldLabel label="Dimension of square in metres:" />
            <Input {...register('dimension', { valueAsNumber: true })} className="!fmtm-w-20" type="number" />
          </div>
          {errors?.dimension?.message && <ErrorMessage message={errors.dimension.message as string} />}
        </div>
      )}

      {values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM && (
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <FieldLabel label="Average number of buildings per task:" />
            <Input {...register('average_buildings_per_task', { valueAsNumber: true })} className="!fmtm-w-20" />
          </div>
          {errors?.average_buildings_per_task?.message && (
            <ErrorMessage message={errors.average_buildings_per_task.message as string} />
          )}
        </div>
      )}

      {values.task_split_type &&
        [task_split_type.DIVIDE_ON_SQUARE, task_split_type.TASK_SPLITTING_ALGORITHM].includes(
          values.task_split_type,
        ) && (
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <Button
              ref={generateBtnRef}
              variant="primary-red"
              isLoading={dividedTaskLoading || taskSplittingGeojsonLoading}
              onClick={generateTaskBasedOnSelection}
              disabled={
                (values.task_split_type === task_split_type.DIVIDE_ON_SQUARE && !values.dimension) ||
                (values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM &&
                  !values.average_buildings_per_task)
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
