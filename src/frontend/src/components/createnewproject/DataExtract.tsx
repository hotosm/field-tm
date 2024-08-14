import axios from 'axios';
import { geojson as fgbGeojson } from 'flatgeobuf';
import React, { useEffect, useState } from 'react';
import Button from '@/components/common/Button';
import { useDispatch } from 'react-redux';
import { CommonActions } from '@/store/slices/CommonSlice';
import RadioButton from '@/components/common/RadioButton';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import { useAppSelector } from '@/types/reduxTypes';
import { FormCategoryService } from '@/api/CreateProjectService';
import FileInputComponent from '@/components/common/FileInputComponent';
import DataExtractValidation from '@/components/createnewproject/validation/DataExtractValidation';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { checkGeomTypeInGeojson } from '@/utilfunctions/checkGeomTypeInGeojson';
import { task_split_type } from '@/types/enums';
import { dataExtractGeojsonType } from '@/store/types/ICreateProject';

const dataExtractOptions = [
  { name: 'data_extract', value: 'osm_data_extract', label: 'Use OSM map features' },
  { name: 'data_extract', value: 'custom_data_extract', label: 'Upload custom map features' },
];

const DataExtract = ({ flag, customDataExtractUpload, setCustomDataExtractUpload }) => {
  useDocumentTitle('Create Project: Map Features');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [extractWays, setExtractWays] = useState('');
  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const projectAoiGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const dataExtractGeojson = useAppSelector((state) => state.createproject.dataExtractGeojson);
  const isFgbFetching = useAppSelector((state) => state.createproject.isFgbFetching);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 5 }));

    // First go to next page, to not block UX
    navigate('/split-tasks');
  };

  const resetFile = (setDataExtractToState) => {
    setDataExtractToState(null);
  };

  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, DataExtractValidation);

  const getFileFromGeojson = (geojson) => {
    // Create a File object from the geojson Blob
    const geojsonBlob = new Blob([JSON.stringify(geojson)], { type: 'application/json' });
    return new File([geojsonBlob], 'data.geojson', { type: 'application/json' });
  };

  // Generate OSM data extract
  const generateDataExtract = async () => {
    if (extractWays !== 'osm_data_extract') {
      return;
    }

    // Remove current data extract
    dispatch(CreateProjectActions.setDataExtractGeojson(null));

    const dataExtractRequestFormData = new FormData();
    const projectAoiGeojsonFile = getFileFromGeojson(projectAoiGeojson);
    dataExtractRequestFormData.append('geojson_file', projectAoiGeojsonFile);
    dataExtractRequestFormData.append('form_category', projectDetails.formCategorySelection);

    // Set flatgeobuf as loading
    dispatch(CreateProjectActions.SetFgbFetchingStatus(true));

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/projects/generate-data-extract/`,
        dataExtractRequestFormData,
      );

      const fgbUrl = response.data.url;
      // Append url to project data & remove custom files
      dispatch(
        CreateProjectActions.SetIndividualProjectDetailsData({
          ...formValues,
          data_extract_url: fgbUrl,
          dataExtractWays: extractWays,
          customDataExtractUpload: null,
        }),
      );

      // Extract fgb and set geojson to map
      const fgbFile = await fetch(fgbUrl);
      const binaryData = await fgbFile.arrayBuffer();
      const uint8ArrayData = new Uint8Array(binaryData);
      // Deserialize the binary data
      const geojsonExtract = await fgbGeojson.deserialize(uint8ArrayData);
      if ((geojsonExtract && (geojsonExtract as dataExtractGeojsonType))?.features?.length > 0) {
        dispatch(CreateProjectActions.SetFgbFetchingStatus(false));
        await dispatch(CreateProjectActions.setDataExtractGeojson(geojsonExtract));
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Map has no features. Please try adjusting the map area.',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.SetFgbFetchingStatus(false));
      }
    } catch (error) {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'Error generating map features.',
          variant: 'error',
          duration: 2000,
        }),
      );
      dispatch(CreateProjectActions.SetFgbFetchingStatus(false));
      // TODO add error message for user
    }
  };

  useEffect(() => {
    if (formValues?.dataExtractWays) {
      setExtractWays(formValues?.dataExtractWays);
    }
  }, [formValues?.dataExtractWays]);

  const toggleStep = (step, url) => {
    if (url === '/select-category') {
      dispatch(
        CreateProjectActions.SetIndividualProjectDetailsData({
          ...formValues,
          dataExtractWays: extractWays,
        }),
      );
    }
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };

  const convertFileToFeatureCol = async (file) => {
    if (!file) return;
    // Parse file as JSON
    const fileReader = new FileReader();
    const fileLoaded: any = await new Promise((resolve) => {
      fileReader.onload = (e) => resolve(e.target?.result);
      fileReader.readAsText(file, 'UTF-8');
    });
    const parsedJSON = JSON.parse(fileLoaded);

    // Convert to FeatureCollection
    let geojsonConversion;
    if (parsedJSON.type === 'FeatureCollection') {
      geojsonConversion = parsedJSON;
    } else if (parsedJSON.type === 'Feature') {
      geojsonConversion = {
        type: 'FeatureCollection',
        features: [parsedJSON],
      };
    } else {
      geojsonConversion = {
        type: 'FeatureCollection',
        features: [{ type: 'Feature', properties: null, geometry: parsedJSON }],
      };
    }
    return geojsonConversion;
  };

  const changeFileHandler = async (event, setDataExtractToState) => {
    const { files } = event.target;
    const uploadedFile = files[0];
    const fileType = uploadedFile.name.split('.').pop();

    // Handle geojson and fgb types, return featurecollection geojson
    let extractFeatCol;
    if (['json', 'geojson'].includes(fileType)) {
      // Set to state immediately for splitting
      setDataExtractToState(uploadedFile);
      extractFeatCol = await convertFileToFeatureCol(uploadedFile);
    } else if (['fgb'].includes(fileType)) {
      const arrayBuffer = new Uint8Array(await uploadedFile.arrayBuffer());
      extractFeatCol = fgbGeojson.deserialize(arrayBuffer);
      // Set converted geojson to state for splitting
      const geojsonFile = new File([extractFeatCol], 'custom_extract.geojson', { type: 'application/json' });
      setDataExtractToState(geojsonFile);
    }
    const hasGeojsonLineString = checkGeomTypeInGeojson(extractFeatCol, 'LineString');
    if (extractFeatCol && extractFeatCol?.features?.length > 0) {
      handleCustomChange('customDataExtractUpload', event.target.files[0]);
      handleCustomChange('hasGeojsonLineString', hasGeojsonLineString);
      handleCustomChange('task_split_type', task_split_type['choose_area_as_task'].toString());
      if (!hasGeojsonLineString) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message:
              'Features must contain line data (roads, rivers) otherwise the task splitting algorithm will not work.',
            variant: 'warning',
            duration: 8000,
          }),
        );
      }
      // View on map
      await dispatch(CreateProjectActions.setDataExtractGeojson(extractFeatCol));
      return;
    }
    dispatch(CommonActions.SetSnackBar({ open: true, message: 'Invalid GeoJSON', variant: 'error', duration: 4000 }));
    handleCustomChange('customDataExtractUpload', null);
    dispatch(CreateProjectActions.setDataExtractGeojson(null));
    return;
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6 lg:fmtm-h-full lg:fmtm-overflow-y-scroll lg:scrollbar">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Map Features</h6>
        <p className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>You may either choose to use OSM data, or upload your own data for the mapping project.</span>
          <span> The relevant map features that exist on OSM are imported based on the select map area.</span>{' '}
          <span>
            You can use these map features to use the 'select from map' functionality from ODK that allows you to select
            the feature to collect data for.
          </span>{' '}
        </p>
      </div>
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <form
            onSubmit={handleSubmit}
            className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between"
          >
            <div>
              <RadioButton
                topic="You may choose to use OSM data or upload your own map features"
                options={dataExtractOptions}
                direction="column"
                value={formValues.dataExtractWays}
                onChangeData={(value) => {
                  handleCustomChange('dataExtractWays', value);
                  setExtractWays(value);
                }}
                errorMsg={errors.dataExtractWays}
              />
              {extractWays === 'osm_data_extract' && (
                <Button
                  btnText="Generate Map Features"
                  btnType="primary"
                  onClick={() => {
                    resetFile(setCustomDataExtractUpload);
                    generateDataExtract();
                  }}
                  className="fmtm-mt-6"
                  isLoading={isFgbFetching}
                  loadingText="Generating Map Features..."
                  disabled={dataExtractGeojson && customDataExtractUpload ? true : false}
                />
              )}
              {extractWays === 'custom_data_extract' && (
                <>
                  <FileInputComponent
                    onChange={(e) => {
                      changeFileHandler(e, setCustomDataExtractUpload);
                    }}
                    onResetFile={() => {
                      resetFile(setCustomDataExtractUpload);
                      handleCustomChange('customDataExtractUpload', null);
                      dispatch(CreateProjectActions.setDataExtractGeojson(null));
                    }}
                    customFile={customDataExtractUpload}
                    btnText="Upload Map Features"
                    accept=".geojson,.json,.fgb"
                    fileDescription="*The supported file formats are .geojson, .json, .fgb"
                    errorMsg={errors.customDataExtractUpload}
                  />
                </>
              )}
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => toggleStep(3, '/select-category')}
                className="fmtm-font-bold"
              />
              <Button
                btnText="NEXT"
                btnType="primary"
                type="submit"
                className="fmtm-font-bold"
                dataTip={`${!dataExtractGeojson ? 'Please Generate Map Features First.' : ''}`}
                disabled={
                  !dataExtractGeojson || (extractWays === 'osm_data_extract' && !dataExtractGeojson) || isFgbFetching
                    ? true
                    : false
                }
              />
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
