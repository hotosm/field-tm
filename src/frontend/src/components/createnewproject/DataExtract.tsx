import React, { useEffect } from 'react';
import Button from '../../components/common/Button';
import { useDispatch } from 'react-redux';
import { CommonActions } from '../../store/slices/CommonSlice';
import RadioButton from '../../components/common/RadioButton';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import useForm from '../../hooks/useForm';
import { useAppSelector } from '../../types/reduxTypes';
import { FormCategoryService } from '../../api/CreateProjectService';
import FileInputComponent from '../../components/common/FileInputComponent';
import DataExtractValidation from './validation/DataExtractValidation';
import NewDefineAreaMap from '../../views/NewDefineAreaMap';

const dataExtractOptions = [
  { name: 'data_extract', value: 'osm_data_extract', label: 'Use OSM data extract' },
  { name: 'data_extract', value: 'custom_data_extract', label: 'Upload custom data extract' },
];

const osmFeatureTypeOptions = [
  { name: 'osm_feature_type', value: 'point_centroid', label: 'Point/Centroid' },
  { name: 'osm_feature_type', value: 'line', label: 'Line' },
  { name: 'osm_feature_type', value: 'polygon', label: 'Polygon' },
];

const DataExtract = ({ flag, customLineUpload, setCustomLineUpload, customPolygonUpload, setCustomPolygonUpload }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const buildingGeojson = useAppSelector((state) => state.createproject.buildingGeojson);
  const lineGeojson = useAppSelector((state) => state.createproject.lineGeojson);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 5 }));
    navigate('/split-tasks');
  };
  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, DataExtractValidation);

  const toggleStep = (step, url) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };
  const changeFileHandler = (event, setFileUploadToState, fileType) => {
    const { files } = event.target;
    setFileUploadToState(files[0]);
    convertFileToGeojson(files[0], fileType);
  };

  const resetFile = (setFileUploadToState) => {
    setFileUploadToState(null);
  };
  const convertFileToGeojson = async (file, fileType) => {
    if (!file) return;
    const fileReader = new FileReader();
    const fileLoaded = await new Promise((resolve) => {
      fileReader.onload = (e) => resolve(e.target.result);
      fileReader.readAsText(file, 'UTF-8');
    });
    const parsedJSON = JSON.parse(fileLoaded);
    let geojsonConversion;
    if (parsedJSON.type === 'FeatureCollection') {
      geojsonConversion = parsedJSON;
    } else {
      geojsonConversion = {
        type: 'FeatureCollection',
        features: [{ type: 'Feature', properties: null, geometry: parsedJSON }],
      };
    }
    if (fileType === 'building') {
      dispatch(CreateProjectActions.SetBuildingGeojson(geojsonConversion));
    } else if (fileType === 'line') {
      dispatch(CreateProjectActions.SetLineGeojson(geojsonConversion));
    }
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Data Extract</h6>
        <p className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>
            You may choose to use the default OSM data extracts as your feature types to perform the field survey
          </span>
          <span>The relevant data extracts that exist on OSM are imported based on your AOI.</span>
          <span>
            You can use these data extracts to use the select_from_map functionality from ODK that allows you the mapper
            to select the existing feature and conduct field mapping survey
          </span>
          <span>
            In contrast to OSM data extracts, you can also upload custom data extracts around the AOI to conduct the
            field mapping survey.
          </span>
          <span>Note: The custom data extracts shall follow the defined data standards.</span>
        </p>
      </div>
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] lg:fmtm-h-[60vh] xl:fmtm-h-[58vh] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <form
            onSubmit={handleSubmit}
            className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between"
          >
            <div>
              {/* <div className="fmtm-mb-5">
                <CustomSelect
                  title="Select form category"
                  placeholder="Select form category"
                  data={formCategoryList}
                  dataKey="id"
                  valueKey="id"
                  label="title"
                  value={formValues.formCategorySelection}
                  onValueChange={(value) => {
                    handleCustomChange('formCategorySelection', value);
                  }}
                />
              </div> */}
              <RadioButton
                topic="You may choose to use OSM data or upload your own data extract"
                options={dataExtractOptions}
                direction="column"
                value={formValues.dataExtractWays}
                onChangeData={(value) => {
                  handleCustomChange('dataExtractWays', value);
                }}
                errorMsg={errors.dataExtractWays}
              />
              {formValues.dataExtractWays === 'osm_data_extract' && (
                <div className="fmtm-mt-6">
                  <RadioButton
                    topic="Select OSM feature type"
                    options={osmFeatureTypeOptions}
                    direction="column"
                    value={formValues.dataExtractFeatureType}
                    onChangeData={(value) => {
                      handleCustomChange('dataExtractFeatureType', value);
                    }}
                    errorMsg={errors.dataExtractFeatureType}
                  />
                </div>
              )}
              {formValues.dataExtractWays === 'custom_data_extract' && (
                <>
                  <FileInputComponent
                    onChange={(e) => {
                      changeFileHandler(e, setCustomPolygonUpload, 'building');
                      handleCustomChange('customPolygonUpload', e.target.files[0]);
                    }}
                    onResetFile={() => resetFile(setCustomPolygonUpload)}
                    customFile={customPolygonUpload}
                    btnText="Upload a Polygon"
                    accept=".geojson,.json"
                    fileDescription="*The supported file formats are .geojson, .json"
                    errorMsg={errors.customPolygonUpload}
                  />
                  <FileInputComponent
                    onChange={(e) => {
                      changeFileHandler(e, setCustomLineUpload, 'line');
                      handleCustomChange('customLineUpload', e.target.files[0]);
                    }}
                    onResetFile={() => resetFile(setCustomLineUpload)}
                    customFile={customLineUpload}
                    btnText="Upload a Line"
                    accept=".geojson,.json"
                    fileDescription="*The supported file formats are .geojson, .json"
                    errorMsg={errors.setCustomLineUpload}
                  />
                </>
              )}
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => toggleStep(3, '/select-form')}
                className="fmtm-font-bold"
              />
              <Button btnText="NEXT" btnType="primary" type="submit" className="fmtm-font-bold" />
            </div>
          </form>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full">
            <NewDefineAreaMap
              uploadedOrDrawnGeojsonFile={drawnGeojson}
              buildingExtractedGeojson={buildingGeojson}
              lineExtractedGeojson={lineGeojson}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataExtract;
