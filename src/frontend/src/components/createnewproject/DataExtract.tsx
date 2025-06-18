import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { geojson as fgbGeojson } from 'flatgeobuf';
import Button from '@/components/common/Button';
import { CommonActions } from '@/store/slices/CommonSlice';
import RadioButton from '@/components/common/RadioButton';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { FormCategoryService } from '@/api/CreateProjectService';
import DataExtractValidation from '@/components/createnewproject/validation/DataExtractValidation';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { task_split_type } from '@/types/enums';
import { dataExtractGeojsonType } from '@/store/types/ICreateProject';
import { CustomCheckbox } from '@/components/common/Checkbox';
import DescriptionSection from '@/components/createnewproject/Description';
import UploadArea from '@/components/common/UploadArea';
import { convertFileToGeojson } from '@/utilfunctions/convertFileToGeojson';
import { fileType } from '@/store/types/ICommon';
import { valid } from 'geojson-validation';
import type { FeatureCollection } from 'geojson';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const primaryGeomOptions = [
  { name: 'primary_geom_type', value: 'POLYGON', label: 'Polygons (e.g. buildings)' },
  { name: 'primary_geom_type', value: 'POINT', label: 'Points (e.g. POIs)' },
  { name: 'primary_geom_type', value: 'POLYLINE', label: 'Lines (e.g. roads, rivers)' },
];

const newGeomOptions = [
  { name: 'new_geom_type', value: 'POLYGON', label: 'Polygons' },
  { name: 'new_geom_type', value: 'POINT', label: 'Points' },
  { name: 'new_geom_type', value: 'POLYLINE', label: 'Lines' },
];

const DataExtract = ({ flag, customDataExtractUpload, setCustomDataExtractUpload }) => {
  useDocumentTitle('Create Project: Map Data');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [disableNextButton, setDisableNextButton] = useState(true);
  const [extractType, setExtractType] = useState('');
  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const projectAoiGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const dataExtractGeojson = useAppSelector((state) => state.createproject.dataExtractGeojson);
  const isFgbFetching = useAppSelector((state) => state.createproject.isFgbFetching);

  useEffect(() => {
    // Creating project without data extract, allow to continue
    if (extractType === 'no_data_extract') {
      setDisableNextButton(false);
      return;
    }

    // No data extract geojson provided, although specified
    if (!dataExtractGeojson) {
      setDisableNextButton(true);
      return;
    }
    const featureCount = dataExtractGeojson?.features?.length ?? 0;

    if (featureCount > 30000) {
      setDisableNextButton(true);
      dispatch(
        CommonActions.SetSnackBar({
          message: `${featureCount} is a lot of features! Please consider breaking this into smaller projects.`,
          variant: 'error',
          duration: 10000,
        }),
      );
      return;
    }

    if (featureCount > 10000) {
      dispatch(
        CommonActions.SetSnackBar({
          message: `${featureCount} is a lot of features to map at once. Are you sure?`,
          variant: 'warning',
          duration: 10000,
        }),
      );
    }

    setDisableNextButton(false);
  }, [dataExtractGeojson, extractType, isFgbFetching]);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 5 }));

    // First go to next page, to not block UX
    navigate('/split-tasks');
  };

  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, DataExtractValidation);

  const dataExtractOptions = [
    {
      name: 'data_extract',
      value: 'osm_data_extract',
      label: 'Fetch data from OSM',
      disabled: formValues.primaryGeomType === 'POLYLINE',
    },
    { name: 'data_extract', value: 'custom_data_extract', label: 'Upload custom map data' },
    { name: 'data_extract', value: 'no_data_extract', label: 'No existing data' },
  ];

  const getFileFromGeojson = (geojson) => {
    // Create a File object from the geojson Blob
    const geojsonBlob = new Blob([JSON.stringify(geojson)], { type: 'application/json' });
    return new File([geojsonBlob], 'data.geojson', { type: 'application/json' });
  };

  // Generate OSM data extract
  const generateDataExtract = async () => {
    if (extractType !== 'osm_data_extract') {
      return;
    }

    // Remove current data extract
    dispatch(CreateProjectActions.setDataExtractGeojson(null));

    const dataExtractRequestFormData = new FormData();
    const projectAoiGeojsonFile = getFileFromGeojson(projectAoiGeojson);
    dataExtractRequestFormData.append('geojson_file', projectAoiGeojsonFile);
    if (projectDetails.osmFormSelectionName) {
      dataExtractRequestFormData.append('osm_category', projectDetails.osmFormSelectionName);
    }
    dataExtractRequestFormData.append('geom_type', formValues.primaryGeomType);

    if (formValues.primaryGeomType == 'POINT') {
      dataExtractRequestFormData.append('centroid', formValues.includeCentroid);
    }

    // Set flatgeobuf as loading
    dispatch(CreateProjectActions.SetFgbFetchingStatus(true));

    try {
      const response = await axios.post(`${VITE_API_URL}/projects/generate-data-extract`, dataExtractRequestFormData);

      const dataExtractGeojsonUrl = response.data.url;
      // Append url to project data & remove custom files
      dispatch(
        CreateProjectActions.SetIndividualProjectDetailsData({
          ...formValues,
          dataExtractType: extractType,
          customDataExtractUpload: null,
        }),
      );

      // Extract fgb and set geojson to map
      const geojsonExtractFile = await fetch(dataExtractGeojsonUrl);
      const geojsonExtract = await geojsonExtractFile.json();
      if ((geojsonExtract && (geojsonExtract as dataExtractGeojsonType))?.features?.length > 0) {
        dispatch(CreateProjectActions.SetFgbFetchingStatus(false));
        await dispatch(CreateProjectActions.setDataExtractGeojson(geojsonExtract));
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Map has no features. Please try adjusting the map area.',
          }),
        );
        dispatch(CreateProjectActions.SetFgbFetchingStatus(false));
      }
    } catch (error) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'Error generating map data.',
        }),
      );
      dispatch(CreateProjectActions.SetFgbFetchingStatus(false));
      // TODO add error message for user
    }
  };

  useEffect(() => {
    if (formValues?.dataExtractType) {
      setExtractType(formValues?.dataExtractType);
    }
  }, [formValues?.dataExtractType]);

  const toggleStep = (step, url) => {
    if (url === '/upload-survey') {
      dispatch(
        CreateProjectActions.SetIndividualProjectDetailsData({
          ...formValues,
          dataExtractType: extractType,
        }),
      );
    }
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };

  const resetMapDataFile = () => {
    setCustomDataExtractUpload(null);
    handleCustomChange('customDataExtractUpload', null);
    dispatch(CreateProjectActions.setDataExtractGeojson(null));
  };

  const changeMapDataFileHandler = async (file: fileType, fileInputRef: React.RefObject<HTMLInputElement | null>) => {
    if (!file) {
      resetMapDataFile();
      return;
    }
    const uploadedFile = file?.file;
    const fileType = uploadedFile.name.split('.').pop();

    // Handle geojson and fgb types, return featurecollection geojson
    let extractFeatCol;
    if (fileType && ['json', 'geojson'].includes(fileType)) {
      // already geojson format, so we simply append
      setCustomDataExtractUpload(file);
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
      setCustomDataExtractUpload(geojsonFromFgbFile);
    }

    validateDataExtractGeojson(extractFeatCol, uploadedFile, fileInputRef);
  };

  const validateDataExtractGeojson = (
    extractFeatCol: FeatureCollection,
    uploadedFile: File,
    fileInputRef: React.RefObject<HTMLInputElement | null>,
  ) => {
    const isGeojsonValid = valid(extractFeatCol, true);

    if (isGeojsonValid?.length === 0 && extractFeatCol) {
      handleCustomChange('customDataExtractUpload', uploadedFile);
      handleCustomChange('task_split_type', task_split_type.CHOOSE_AREA_AS_TASK.toString());
      dispatch(CreateProjectActions.setDataExtractGeojson(extractFeatCol));
    } else {
      resetMapDataFile();
      if (fileInputRef.current) fileInputRef.current.value = '';
      dispatch(
        CommonActions.SetSnackBar({
          message: `The uploaded GeoJSON is invalid and contains the following errors: ${isGeojsonValid?.map((error) => `\n${error}`)}`,
          duration: 10000,
        }),
      );
    }
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${VITE_API_URL}/central/list-forms`));
  }, []);

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
      <DescriptionSection section="Map Data" />
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <form
            onSubmit={handleSubmit}
            className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between"
          >
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
              <label className="fmtm-text-sm font-medium">What type of geometry do you wish to map?</label>
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
                {primaryGeomOptions.map((option) => (
                  <div key={option.value} className="fmtm-flex fmtm-flex-col">
                    <label className="fmtm-flex fmtm-items-center fmtm-gap-2">
                      <input
                        type="radio"
                        name="primary_geom_type"
                        value={option.value}
                        checked={formValues.primaryGeomType === option.value}
                        onChange={(e) => {
                          handleCustomChange('primaryGeomType', e.target.value);
                          handleCustomChange('dataExtractType', null);
                        }}
                      />
                      {option.label}
                    </label>

                    {option.value === 'POINT' && formValues.primaryGeomType === 'POINT' && (
                      <div className="fmtm-ml-8 fmtm-mt-1 fmtm-flex fmtm-items-center fmtm-gap-2">
                        <input
                          type="checkbox"
                          id="includeCentroid"
                          checked={formValues.includeCentroid || false}
                          onChange={(e) => handleCustomChange('includeCentroid', e.target.checked)}
                        />
                        <label htmlFor="includeCentroid" className="fmtm-text-sm">
                          Include polygon centroids
                        </label>
                      </div>
                    )}
                  </div>
                ))}
                {errors.primaryGeomType && (
                  <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.primaryGeomType}</p>
                )}
              </div>

              <CustomCheckbox
                key="newFeatureType"
                label="I want to use a mix of geometry types"
                checked={formValues?.useMixedGeomTypes}
                onCheckedChange={(status) => {
                  handleCustomChange('useMixedGeomTypes', status);
                }}
                className="fmtm-text-black"
                labelClickable
              />
              {formValues?.useMixedGeomTypes && (
                <>
                  <RadioButton
                    topic="New geometries collected should be of type"
                    options={newGeomOptions}
                    direction="column"
                    value={formValues.newGeomType}
                    onChangeData={(value) => {
                      handleCustomChange('newGeomType', value);
                    }}
                    errorMsg={errors.newGeomType}
                    required
                  />
                </>
              )}
              <RadioButton
                topic="Upload your own map data or use OSM"
                options={dataExtractOptions}
                direction="column"
                value={formValues.dataExtractType}
                onChangeData={(value) => {
                  handleCustomChange('dataExtractType', value);
                  setExtractType(value);
                }}
                errorMsg={errors.dataExtractType}
                hoveredOption={(hoveredOption) =>
                  dispatch(
                    CreateProjectActions.SetDescriptionToFocus(
                      hoveredOption && hoveredOption === 'osm_data_extract' ? 'mapfeatures-osm' : null,
                    ),
                  )
                }
                required
              />
              {extractType === 'osm_data_extract' && (
                <Button
                  variant="primary-red"
                  onClick={() => {
                    setCustomDataExtractUpload(null);
                    generateDataExtract();
                  }}
                  isLoading={isFgbFetching}
                  disabled={dataExtractGeojson && customDataExtractUpload ? true : false}
                >
                  Fetch OSM Data
                </Button>
              )}
              {extractType === 'custom_data_extract' && (
                <>
                  <UploadArea
                    title="Upload Map Data"
                    label="The supported file formats are .geojson, .json, .fgb"
                    data={customDataExtractUpload ? [customDataExtractUpload] : []}
                    onUploadFile={(updatedFiles, fileInputRef) => {
                      changeMapDataFileHandler(updatedFiles?.[0] as fileType, fileInputRef);
                    }}
                    acceptedInput=".geojson,.json,.fgb"
                  />
                </>
              )}
              <p className="fmtm-text-gray-500">
                Total number of features:{' '}
                <span className="fmtm-font-bold">{dataExtractGeojson?.features?.length || 0}</span>
              </p>
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button variant="secondary-grey" onClick={() => toggleStep(3, '/upload-survey')}>
                PREVIOUS
              </Button>
              <Button variant="primary-red" type="submit" disabled={disableNextButton}>
                NEXT
              </Button>
            </div>
          </form>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full">
            <NewDefineAreaMap
              uploadedOrDrawnGeojsonFile={projectAoiGeojson}
              buildingExtractedGeojson={dataExtractGeojson}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataExtract;
