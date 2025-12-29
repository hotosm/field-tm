import React, { useEffect, useState } from 'react';
import { z } from 'zod/v4';
import { Controller, useFormContext } from 'react-hook-form';
import { geojson as fgbGeojson } from 'flatgeobuf';
import { valid } from 'geojson-validation';
import type { FeatureCollection } from 'geojson';

import { CommonActions } from '@/store/slices/CommonSlice';
import { dataExtractGeojsonType } from '@/store/types/ICreateProject';
import { convertFileToGeojson } from '@/utilfunctions/convertFileToGeojson';
import { data_extract_type, task_split_type } from '@/types/enums';
import { useAppDispatch } from '@/types/reduxTypes';
import { createProjectValidationSchema } from './validation';
import FieldLabel from '@/components/common/FieldLabel';
import RadioButton from '@/components/common/RadioButton';
import Switch from '@/components/common/Switch';
import Button from '@/components/common/Button';
import ErrorMessage from '@/components/common/ErrorMessage';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useGenerateDataExtractMutation } from '@/api/project';
import FileUpload from '@/components/common/FileUpload';
import isEmpty from '@/utilfunctions/isEmpty';
import { FileType } from '@/types';
import { TooltipMessage } from './constants/TooltipMessage';

const MapData = () => {
  useDocumentTitle('Create Project: Map Data');

  const dispatch = useAppDispatch();

  const form = useFormContext<z.infer<typeof createProjectValidationSchema>>();
  const { watch, control, setValue, formState } = form;
  const { errors } = formState;
  const values = watch();
  const [fetchingOSMData, setFetchingOSMData] = useState(false);

  const dataExtractOptions = [
    {
      name: 'data_extract',
      value: data_extract_type.OSM,
      label: 'Fetch data from OSM',
      disabled:
        values.outlineArea && +values.outlineArea?.split(' ')?.[0] > 200 && values.outlineArea?.split(' ')[1] === 'km²',
    },
    { name: 'data_extract', value: data_extract_type.CUSTOM, label: 'Upload custom map data' },
    { name: 'data_extract', value: data_extract_type.NONE, label: 'No existing data' },
  ];

  const changeFileHandler = async (file: FileType[]) => {
    if (isEmpty(file)) return;

    if (values.splitGeojsonByAlgorithm) {
      setValue('splitGeojsonByAlgorithm', null);
    }

    const uploadedFile = file?.[0]?.file;
    const fileType = uploadedFile.name.split('.').pop();

    // Handle geojson and fgb types, return featurecollection geojson
    let extractFeatCol;
    if (fileType && ['json', 'geojson'].includes(fileType)) {
      // already geojson format, so we simply append
      setValue('customDataExtractFile', file);
      extractFeatCol = await convertFileToGeojson(uploadedFile);
    } else if (fileType && ['fgb'].includes(fileType)) {
      // deserialise the fgb --> geojson for upload
      const arrayBuffer = new Uint8Array(await uploadedFile.arrayBuffer());
      extractFeatCol = fgbGeojson.deserialize(arrayBuffer);
      // Set converted geojson to state for splitting
      const geojsonFromFgbFile = {
        ...file,
        file: new File([JSON.stringify(extractFeatCol)], 'custom_extract.geojson', { type: 'application/json' }),
      };
      setValue('customDataExtractFile', geojsonFromFgbFile);
    }

    validateDataExtractGeojson(extractFeatCol);
  };

  const resetMapDataFile = () => {
    setValue('customDataExtractFile', []);
    setValue('dataExtractGeojson', null);
    if (values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM) {
      setValue('task_split_type', null);
      setValue('splitGeojsonByAlgorithm', null);
    }
  };

  const validateDataExtractGeojson = (extractFeatCol: FeatureCollection<null, Record<string, any>>) => {
    const isGeojsonValid = valid(extractFeatCol, true);
    if (isGeojsonValid?.length === 0 && extractFeatCol) {
      setValue('dataExtractGeojson', { ...extractFeatCol, id: values.osm_category });
    } else {
      resetMapDataFile();
      dispatch(
        CommonActions.SetSnackBar({
          message: `The uploaded GeoJSON is invalid and contains the following errors: ${isGeojsonValid?.map((error) => `\n${error}`)}`,
          duration: 10000,
        }),
      );
    }
  };

  // Create a File object from the geojson Blob
  const getFileFromGeojson = (geojson) => {
    const geojsonBlob = new Blob([JSON.stringify(geojson)], { type: 'application/json' });
    return new File([geojsonBlob], 'data.geojson', { type: 'application/json' });
  };

  const { mutate: generateDataExtractMutate, isPending: isGeneratingDataExtract } = useGenerateDataExtractMutation({
    onSuccess: async ({ data }) => {
      setFetchingOSMData(true);
      const dataExtractGeojsonUrl = data?.url;
      // Extract fgb and set geojson to map
      const geojsonExtractFile = await fetch(dataExtractGeojsonUrl);
      const geojsonExtract = await geojsonExtractFile.json();
      if ((geojsonExtract && (geojsonExtract as dataExtractGeojsonType))?.features?.length > 0) {
        setValue('dataExtractGeojson', { ...geojsonExtract, id: values.osm_category });
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Map has no features. Please try adjusting the map area.',
          }),
        );
      }
      if (values.splitGeojsonByAlgorithm) {
        setValue('splitGeojsonByAlgorithm', null);
      }
      setFetchingOSMData(false);
    },
    onError: ({ response }) => {
      dispatch(CommonActions.SetSnackBar({ message: response?.data?.detail || 'Failed to generate data extract' }));
    },
  });

  // Generate OSM data extract
  const generateDataExtract = async () => {
    const dataExtractRequestFormData = new FormData();
    const projectAoiGeojsonFile = getFileFromGeojson(values.outline);

    dataExtractRequestFormData.append('geojson_file', projectAoiGeojsonFile);
    dataExtractRequestFormData.append('osm_category', values.osm_category);
    dataExtractRequestFormData.append('use_st_within', (!values.use_st_within)?.toString() ?? 'false');

    generateDataExtractMutate({ payload: dataExtractRequestFormData, params: { project_id: values.id! } });
  };

  useEffect(() => {
    if (!values.dataExtractGeojson) return;
    const featureCount = values.dataExtractGeojson?.features?.length ?? 0;

    if (featureCount > 30000) {
      dispatch(
        CommonActions.SetSnackBar({
          message: `${featureCount} is a lot of features! Please consider breaking this into smaller projects.`,
          variant: 'error',
          duration: 10000,
        }),
      );
    } else if (featureCount > 10000) {
      dispatch(
        CommonActions.SetSnackBar({
          message: `${featureCount} is a lot of features to map at once. Are you sure?`,
          variant: 'warning',
          duration: 10000,
        }),
      );
    }
  }, [values.dataExtractGeojson]);

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-[1.125rem] fmtm-w-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <FieldLabel
          label="Upload your own map data or use OSM"
          astric
          tooltipMessage={<TooltipMessage name="UploadMapData" />}
        />
        <Controller
          control={control}
          name="dataExtractType"
          render={({ field }) => (
            <RadioButton
              value={field.value || ''}
              options={dataExtractOptions}
              onChangeData={(value) => {
                field.onChange(value);
                if (value === data_extract_type.NONE) resetMapDataFile();
              }}
              ref={field.ref}
            />
          )}
        />
        {errors?.dataExtractType?.message && <ErrorMessage message={errors.dataExtractType.message as string} />}
      </div>

      {values.dataExtractType === 'osm_data_extract' && (
        <>
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <FieldLabel label="Allow Features that intersect the AOI" />
            <Controller
              control={control}
              name="use_st_within"
              render={({ field }) => (
                <Switch
                  ref={field.ref}
                  checked={field.value}
                  onCheckedChange={(value) => {
                    field.onChange(value);
                    setValue('use_st_within', value);
                  }}
                  className=""
                />
              )}
            />
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            <Button
              variant="primary-red"
              onClick={() => {
                resetMapDataFile();
                generateDataExtract();
              }}
              isLoading={isGeneratingDataExtract || fetchingOSMData}
            >
              Fetch OSM Data
            </Button>
          </div>
        </>
      )}

      {values.dataExtractType === 'custom_data_extract' && (
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <FieldLabel label="Upload Map Data" astric />
          <FileUpload
            onChange={changeFileHandler}
            onDelete={resetMapDataFile}
            data={values.customDataExtractFile}
            fileAccept=".geojson,.json,.fgb"
            placeholder="The supported file formats are .geojson, .json, .fgb"
          />
          {errors?.customDataExtractFile?.message && (
            <ErrorMessage message={errors.customDataExtractFile.message as string} />
          )}
        </div>
      )}

      {errors?.dataExtractGeojson?.message && <ErrorMessage message={errors.dataExtractGeojson.message as string} />}

      {values.dataExtractGeojson && (
        <p className="fmtm-text-gray-500 fmtm-text-sm">
          Total number of features:{' '}
          <span className="fmtm-font-bold">{values.dataExtractGeojson?.features?.length || 0}</span>
        </p>
      )}
    </div>
  );
};

export default MapData;
