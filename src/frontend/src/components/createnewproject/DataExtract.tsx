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
import FileInputComponent from '@/components/common/FileInputComponent';
import DataExtractValidation from '@/components/createnewproject/validation/DataExtractValidation';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { task_split_type } from '@/types/enums';
import { dataExtractGeojsonType } from '@/store/types/ICreateProject';
import { CustomCheckbox } from '@/components/common/Checkbox';
import DescriptionSection from '@/components/createnewproject/Description';

const dataExtractOptions = [
  { name: 'data_extract', value: 'osm_data_extract', label: 'Fetch data from OSM' },
  { name: 'data_extract', value: 'custom_data_extract', label: 'Upload custom map data' },
];

const DataExtract = ({
  flag,
  customDataExtractUpload,
  setCustomDataExtractUpload,
  additionalFeature,
  setAdditionalFeature,
}) => {
  useDocumentTitle('Create Project: Map Data');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [disableNextButton, setDisableNextButton] = useState(true);
  const [extractWays, setExtractWays] = useState('');
  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const projectAoiGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const dataExtractGeojson = useAppSelector((state) => state.createproject.dataExtractGeojson);
  const isFgbFetching = useAppSelector((state) => state.createproject.isFgbFetching);
  const additionalFeatureGeojson = useAppSelector((state) => state.createproject.additionalFeatureGeojson);

  useEffect(() => {
    const featureCount = dataExtractGeojson?.features?.length ?? 0;

    if (featureCount > 10000) {
      dispatch(
        CommonActions.SetSnackBar({
          message: `${featureCount} is a lot of features to map at once. Are you sure?`,
          variant: 'warning',
          duration: 10000,
        }),
      );
    }

    if (featureCount > 30000) {
      setDisableNextButton(true);
      dispatch(
        CommonActions.SetSnackBar({
          message: `${featureCount} is a lot of features! Please consider breaking this into smaller projects.`,
          variant: 'error',
          duration: 10000,
        }),
      );
    } else {
      // Enable/disable NEXT button based on conditions (if feature limit not exceeded)
      const shouldDisableButton =
        !dataExtractGeojson || (extractWays === 'osm_data_extract' && !dataExtractGeojson) || isFgbFetching;
      setDisableNextButton(shouldDisableButton);
    }
  }, [dataExtractGeojson, additionalFeatureGeojson, extractWays, isFgbFetching]);

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
        `${import.meta.env.VITE_API_URL}/projects/generate-data-extract`,
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
    if (formValues?.dataExtractWays) {
      setExtractWays(formValues?.dataExtractWays);
    }
  }, [formValues?.dataExtractWays]);

  const toggleStep = (step, url) => {
    if (url === '/upload-survey') {
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
    if (extractFeatCol && extractFeatCol?.features?.length > 0) {
      handleCustomChange('customDataExtractUpload', event.target.files[0]);
      handleCustomChange('task_split_type', task_split_type.CHOOSE_AREA_AS_TASK.toString());
      // View on map
      await dispatch(CreateProjectActions.setDataExtractGeojson(extractFeatCol));
      return;
    }
    dispatch(CommonActions.SetSnackBar({ message: 'Invalid GeoJSON' }));
    handleCustomChange('customDataExtractUpload', null);
    dispatch(CreateProjectActions.setDataExtractGeojson(null));
    return;
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
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
            <div>
              <RadioButton
                topic="You may choose to use OSM data or upload your own map data"
                options={dataExtractOptions}
                direction="column"
                value={formValues.dataExtractWays}
                onChangeData={(value) => {
                  handleCustomChange('dataExtractWays', value);
                  setExtractWays(value);
                }}
                errorMsg={errors.dataExtractWays}
                hoveredOption={(hoveredOption) =>
                  dispatch(
                    CreateProjectActions.SetDescriptionToFocus(
                      hoveredOption && hoveredOption === 'osm_data_extract' ? 'mapfeatures-osm' : null,
                    ),
                  )
                }
              />
              {extractWays === 'osm_data_extract' && (
                <div className="fmtm-mt-4 fmtm-mb-8">
                  <Button
                    variant="primary-red"
                    onClick={() => {
                      resetFile(setCustomDataExtractUpload);
                      generateDataExtract();
                    }}
                    isLoading={isFgbFetching}
                    disabled={dataExtractGeojson && customDataExtractUpload ? true : false}
                  >
                    Fetch OSM Data
                  </Button>
                </div>
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
                    btnText="Upload Map Data"
                    accept=".geojson,.json,.fgb"
                    fileDescription="*The supported file formats are .geojson, .json, .fgb"
                    errorMsg={errors.customDataExtractUpload}
                  />
                </>
              )}
              <div className="fmtm-mt-5">
                <p className="fmtm-text-gray-500">
                  Total number of features:{' '}
                  <span className="fmtm-font-bold">{dataExtractGeojson?.features?.length || 0}</span>
                </p>
              </div>
              {extractWays && (
                <div className="fmtm-mt-4">
                  <div
                    onMouseOver={() => {
                      dispatch(CreateProjectActions.SetDescriptionToFocus('mapfeatures-additional'));
                    }}
                    onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
                  >
                    <CustomCheckbox
                      key="uploadAdditionalFeature"
                      label="Upload Supporting Datasets"
                      checked={formValues?.hasAdditionalFeature}
                      onCheckedChange={(status) => {
                        handleCustomChange('hasAdditionalFeature', status);
                        handleCustomChange('additionalFeature', null);
                        dispatch(CreateProjectActions.SetAdditionalFeatureGeojson(null));
                        setAdditionalFeature(null);
                      }}
                      className="fmtm-text-black"
                      labelClickable
                    />
                  </div>
                  {formValues?.hasAdditionalFeature && (
                    <>
                      <FileInputComponent
                        onChange={async (e) => {
                          if (e?.target?.files) {
                            const uploadedFile = e?.target?.files[0];
                            setAdditionalFeature(uploadedFile);
                            handleCustomChange('additionalFeature', uploadedFile);
                            const additionalFeatureGeojson = await convertFileToFeatureCol(uploadedFile);
                            dispatch(CreateProjectActions.SetAdditionalFeatureGeojson(additionalFeatureGeojson));
                          }
                        }}
                        onResetFile={() => {
                          resetFile(setAdditionalFeature);
                          dispatch(CreateProjectActions.SetAdditionalFeatureGeojson(null));
                          handleCustomChange('additionalFeature', null);
                        }}
                        customFile={additionalFeature}
                        btnText="Upload Supporting Datasets"
                        accept=".geojson"
                        fileDescription="*The supported file formats are .geojson"
                        errorMsg={errors.additionalFeature}
                      />
                    </>
                  )}
                  {additionalFeatureGeojson && (
                    <p className="fmtm-text-gray-500 fmtm-mt-1">
                      Total number of additional features:{' '}
                      <span className="fmtm-font-bold">{additionalFeatureGeojson?.features?.length || 0}</span>
                    </p>
                  )}
                </div>
              )}
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
              additionalFeatureGeojson={additionalFeatureGeojson}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataExtract;
