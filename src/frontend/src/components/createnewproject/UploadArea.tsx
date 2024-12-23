import React, { useEffect, useRef, useState } from 'react';
import { CommonActions } from '@/store/slices/CommonSlice';
import Button from '@/components/common/Button';
import { useDispatch } from 'react-redux';
import RadioButton from '@/components/common/RadioButton';
import AssetModules from '@/shared/AssetModules.js';
import DrawSvg from '@/components/createnewproject/DrawSvg';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import { useAppSelector } from '@/types/reduxTypes';
import UploadAreaValidation from '@/components/createnewproject/validation/UploadAreaValidation';
import FileInputComponent from '@/components/common/FileInputComponent';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import { checkWGS84Projection } from '@/utilfunctions/checkWGS84Projection.js';
import { valid } from 'geojson-validation';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import DescriptionSection from '@/components/createnewproject/Description';

const uploadAreaOptions = [
  {
    name: 'upload_area',
    value: 'draw',
    label: 'Draw',
    icon: <DrawSvg />,
  },
  {
    name: 'upload_area',
    value: 'upload_file',
    label: 'Upload File',
    icon: <AssetModules.DriveFolderUploadIcon className="fmtm-text-gray-500" sx={{ height: '30px', width: '30px' }} />,
  },
];

const UploadArea = ({ flag, geojsonFile, setGeojsonFile, setCustomDataExtractUpload, setAdditionalFeature }) => {
  useDocumentTitle('Create Project: Project Area');

  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [isGeojsonWGS84, setIsGeojsonWG84] = useState(true);

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const uploadAreaSelection = useAppSelector((state) => state.createproject.uploadAreaSelection);
  const drawToggle = useAppSelector((state) => state.createproject.drawToggle);
  const totalAreaSelection = useAppSelector((state) => state.createproject.totalAreaSelection);
  const toggleSplittedGeojsonEdit = useAppSelector((state) => state.createproject.toggleSplittedGeojsonEdit);

  const submission = () => {
    if (totalAreaSelection) {
      const totalArea = parseFloat(totalAreaSelection?.split(' ')[0]);
      const areaUnit = totalAreaSelection?.split(' ')[1];
      if (totalArea > 200 && areaUnit === 'km²') {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Cannot create project of project area exceeding 200 Sq.KM.',
            variant: 'error',
            duration: 3000,
          }),
        );
        return;
      }
    }
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 3 }));
    navigate('/upload-survey');
    dispatch(CreateProjectActions.SetToggleSplittedGeojsonEdit(false));
  };

  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, UploadAreaValidation);

  const toggleStep = (step: number, url: string) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
    dispatch(CreateProjectActions.SetToggleSplittedGeojsonEdit(false));
  };

  const convertFileToGeojson = async (file) => {
    if (!file) return;
    const fileReader = new FileReader();
    const fileLoaded: any = await new Promise((resolve) => {
      fileReader.onload = (e) => resolve(e.target?.result);
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
    addGeojsonToState(geojsonConversion);
    return geojsonConversion;
  };

  const addGeojsonToState = (geojson) => {
    dispatch(CreateProjectActions.SetDrawnGeojson(geojson));
  };

  const changeFileHandler = async (event) => {
    const { files } = event.target;
    if (valid(await convertFileToGeojson(files[0]))) {
      handleCustomChange('uploadedAreaFile', files[0].name);
      setGeojsonFile(files[0]);
      convertFileToGeojson(files[0]);
    } else {
      handleCustomChange('uploadedAreaFile', '');
      setGeojsonFile(null);
      addGeojsonToState(null);
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'File not a valid geojson',
          variant: 'error',
          duration: 4000,
        }),
      );
    }
    handleCustomChange('drawnGeojson', null);
    dispatch(CreateProjectActions.SetTotalAreaSelection(null));
  };

  useEffect(() => {
    if (drawnGeojson && !valid(drawnGeojson)) {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'File not a valid geojson',
          variant: 'error',
          duration: 4000,
        }),
      );
      return;
    }
    if (drawnGeojson) {
      const isWGS84 = () => {
        if (uploadAreaSelection === 'upload_file') {
          const isWGS84Projection = checkWGS84Projection(drawnGeojson);
          setIsGeojsonWG84(isWGS84Projection);
          return isWGS84Projection;
        }
        setIsGeojsonWG84(true);
        return true;
      };
      if (!isWGS84() && drawnGeojson) {
        showSpatialError();
      }
    }
    return () => {};
  }, [drawnGeojson]);

  const showSpatialError = () => {
    dispatch(
      CommonActions.SetSnackBar({
        open: true,
        message: 'Invalid spatial reference system. Please only import WGS84 (EPSG: 4326).',
        variant: 'error',
        duration: 6000,
      }),
    );
  };

  const resetFile = () => {
    setGeojsonFile(null);
    setCustomDataExtractUpload(null);
    handleCustomChange('uploadedAreaFile', null);
    handleCustomChange('drawnGeojson', null);
    setAdditionalFeature(null);
    dispatch(CreateProjectActions.SetDrawnGeojson(null));
    dispatch(CreateProjectActions.SetTotalAreaSelection(null));
    dispatch(CreateProjectActions.SetAdditionalFeatureGeojson(null));
    dispatch(CreateProjectActions.ClearProjectStepState({ ...formValues, uploadedAreaFile: null, drawnGeojson: null }));
  };

  useEffect(() => {
    if (totalAreaSelection) {
      const totalArea = parseFloat(totalAreaSelection?.split(' ')[0]);
      const areaUnit = totalAreaSelection?.split(' ')[1];
      if (totalArea > 100 && areaUnit === 'km²') {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'The project area exceeded over 100 Sq.KM.',
            variant: 'warning',
            duration: 3000,
          }),
        );
      }
      if (totalArea > 200 && areaUnit === 'km²') {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'The project area exceeded 200 Sq.KM. and must be less than 200 Sq.KM.',
            variant: 'error',
            duration: 3000,
          }),
        );
      }
    }
  }, [totalAreaSelection]);

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
      <DescriptionSection section="Project Area" />
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-h-full fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!isGeojsonWGS84 && drawnGeojson) {
                showSpatialError();
              } else {
                handleSubmit(e);
              }
            }}
            className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between"
          >
            <div>
              <RadioButton
                topic="Select one of the option to upload area"
                options={uploadAreaOptions}
                direction="row"
                onChangeData={(value) => {
                  handleCustomChange('uploadAreaSelection', value);
                  dispatch(CreateProjectActions.SetUploadAreaSelection(value));
                  if (value === 'draw') {
                    dispatch(CreateProjectActions.SetDrawToggle(!drawToggle));
                  } else {
                    dispatch(CreateProjectActions.SetDrawToggle(false));
                  }
                }}
                value={uploadAreaSelection}
                errorMsg={errors.uploadAreaSelection}
                hoveredOption={(hoveredOption) => {
                  dispatch(
                    CreateProjectActions.SetDescriptionToFocus(hoveredOption ? `uploadarea-${hoveredOption}` : null),
                  );
                }}
              />
              {uploadAreaSelection === 'draw' && (
                <div>
                  <p className="fmtm-text-gray-700 fmtm-pt-5 fmtm-pb-5">Draw a polygon on the map to plot the area</p>
                  <Button
                    btnText="Reset"
                    btnType="secondary"
                    type="button"
                    onClick={() => resetFile()}
                    className=""
                    disabled={drawnGeojson ? false : true}
                  />
                  <p className="fmtm-text-gray-700 fmtm-mt-5">
                    Total Area: <span className="fmtm-font-bold">{totalAreaSelection}</span>
                  </p>
                  {errors.drawnGeojson && (
                    <div>
                      <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.drawnGeojson}</p>
                    </div>
                  )}
                </div>
              )}
              {uploadAreaSelection === 'upload_file' && (
                <div
                  onMouseOver={() => dispatch(CreateProjectActions.SetDescriptionToFocus('uploadarea-uploadgeojson'))}
                  onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
                >
                  <FileInputComponent
                    customFile={geojsonFile}
                    onChange={changeFileHandler}
                    onResetFile={resetFile}
                    accept=".geojson, .json"
                    fileDescription="*The supported file format is geojson file."
                    btnText="Upload a Geojson"
                    errorMsg={errors.uploadedAreaFile}
                  />
                  <p className="fmtm-text-gray-700">
                    Total Area: <span className="fmtm-font-bold">{totalAreaSelection}</span>
                  </p>
                </div>
              )}
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => {
                  dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
                  toggleStep(1, '/create-project');
                }}
                className="fmtm-font-bold"
              />
              <Button btnText="NEXT" btnType="primary" type="submit" className="fmtm-font-bold" />
            </div>
          </form>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-full">
            <NewDefineAreaMap
              drawToggle={drawToggle}
              uploadedOrDrawnGeojsonFile={drawnGeojson}
              onDraw={
                drawnGeojson || uploadAreaSelection === 'upload_file'
                  ? null
                  : (geojson, area) => {
                      handleCustomChange('drawnGeojson', geojson);
                      dispatch(CreateProjectActions.SetDrawnGeojson(JSON.parse(geojson)));
                      dispatch(CreateProjectActions.SetTotalAreaSelection(area));
                      setGeojsonFile(null);
                    }
              }
              onModify={
                toggleSplittedGeojsonEdit
                  ? (geojson, area) => {
                      handleCustomChange('drawnGeojson', geojson);
                      dispatch(CreateProjectActions.SetDrawnGeojson(JSON.parse(geojson)));
                      dispatch(CreateProjectActions.SetTotalAreaSelection(area));
                      dispatch(CreateProjectActions.ClearProjectStepState(formValues));
                      setCustomDataExtractUpload(null);
                    }
                  : null
              }
              getAOIArea={(area) => {
                if (drawnGeojson) {
                  dispatch(CreateProjectActions.SetTotalAreaSelection(area));
                }
              }}
              hasEditUndo
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadArea;
