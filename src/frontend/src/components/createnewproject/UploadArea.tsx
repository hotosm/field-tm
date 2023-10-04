import React, { useEffect, useRef } from 'react';
import { CommonActions } from '../../store/slices/CommonSlice';
import Button from '../../components/common/Button';
import { useDispatch } from 'react-redux';
import RadioButton from '../../components/common/RadioButton';
import AssetModules from '../../shared/AssetModules.js';
import DrawSvg from './DrawSvg';
import { useNavigate } from 'react-router-dom';
import CoreModules from '../../shared/CoreModules';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
// @ts-ignore
const DefineAreaMap = React.lazy(() => import('../../views/DefineAreaMap'));

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

const UploadArea = ({ flag, geojsonFile, setGeojsonFile }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const geojsonFileRef: any = useRef(null);

  const drawnGeojson = CoreModules.useAppSelector((state) => state.createproject.drawnGeojson);
  const uploadAreaSelection = CoreModules.useAppSelector((state) => state.createproject.uploadAreaSelection);
  const drawToggle = CoreModules.useAppSelector((state) => state.createproject.drawToggle);
  const totalAreaSelection = CoreModules.useAppSelector((state) => state.createproject.totalAreaSelection);

  const toggleStep = (step, url) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };

  const changeFileHandler = (event) => {
    const { files } = event.target;
    setGeojsonFile(files[0]);
  };

  const onCreateProjectSubmission = () => {
    if (!drawnGeojson && !geojsonFile) {
      return;
    } else {
      toggleStep(3, '/new-select-form');
    }
  };

  useEffect(() => {
    setGeojsonFile(null);
    dispatch(CreateProjectActions.SetDrawnGeojson(null));
    dispatch(CreateProjectActions.SetTotalAreaSelection(null));
  }, [uploadAreaSelection]);

  const resetFile = () => {
    if (geojsonFileRef.current) {
      geojsonFileRef.current.value = '';
    }
    setGeojsonFile(null);
    dispatch(CreateProjectActions.SetDrawnGeojson(null));
    dispatch(CreateProjectActions.SetTotalAreaSelection(null));
  };

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Upload Area</h6>
        <p className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>Fill in your project basic information such as name, description, hashtag, etc. </span>
          <span>To complete the first step, you will need the account credentials of ODK central server.</span>{' '}
          <span>Here are the instructions for setting up a Central ODK Server on Digital Ocean.</span>
        </p>
      </div>
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] lg:fmtm-h-[60vh] xl:fmtm-h-[58vh] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between">
            <div>
              <RadioButton
                topic="Select one of the option to upload area"
                options={uploadAreaOptions}
                direction="row"
                onChangeData={(value) => {
                  dispatch(CreateProjectActions.SetUploadAreaSelection(value));
                  if (value === 'draw') {
                    dispatch(CreateProjectActions.SetDrawToggle(!drawToggle));
                  } else {
                    dispatch(CreateProjectActions.SetDrawToggle(false));
                  }
                }}
                value={uploadAreaSelection}
              />
              {uploadAreaSelection === 'draw' && (
                <div>
                  <p className="fmtm-text-gray-700 fmtm-pt-5 fmtm-pb-3">Draw a polygon on the map to plot the area</p>
                  <Button
                    btnText="Click to Reset"
                    btnType="primary"
                    type="button"
                    onClick={() => resetFile()}
                    className=""
                  />
                  <p className="fmtm-text-gray-700 fmtm-pt-8">
                    Total Area: <span className="fmtm-font-bold">{totalAreaSelection}</span>
                  </p>
                </div>
              )}
              {uploadAreaSelection === 'upload_file' && (
                <div className="fmtm-mt-5 fmtm-pb-3">
                  <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
                    <label
                      id="file-input"
                      className="fmtm-bg-primaryRed fmtm-text-white fmtm-px-4 fmtm-py-1 fmtm-rounded-md fmtm-cursor-pointer"
                    >
                      <p>Select a file</p>
                      <input
                        id="upload-area-geojson-file"
                        ref={geojsonFileRef}
                        type="file"
                        className="fmtm-hidden"
                        onChange={changeFileHandler}
                        accept=".geojson, .json"
                      />
                    </label>
                    <div className="fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-slate-100 fmtm-duration-300 fmtm-cursor-pointer">
                      <AssetModules.ReplayIcon className="fmtm-text-gray-600" onClick={() => resetFile()} />
                    </div>
                  </div>
                  {geojsonFile && (
                    <div className="fmtm-mt-2">
                      <p>{geojsonFile?.name}</p>
                    </div>
                  )}
                  <p className="fmtm-text-gray-700 fmtm-mt-3">
                    *The supported file formats are zipped shapefile, geojson or kml files.
                  </p>
                  <p className="fmtm-text-gray-700 fmtm-pt-8">
                    Total Area: <span className="fmtm-font-bold">234 sq.km</span>
                  </p>
                </div>
              )}
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => toggleStep(1, '/new-create-project')}
                className="fmtm-font-bold"
              />
              <Button
                btnText="NEXT"
                btnType="primary"
                type="button"
                onClick={() => onCreateProjectSubmission()}
                className="fmtm-font-bold"
              />
            </div>
          </div>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full">
            <DefineAreaMap
              uploadedGeojson={geojsonFile}
              onDraw={(geojson, area) => {
                // dispatch(CreateProjectActions.SetDividedTaskGeojson(JSON.parse(geojson)));
                dispatch(CreateProjectActions.SetDrawnGeojson(JSON.parse(geojson)));
                // setGeojsonFile(JSON.parse(geojson));
                dispatch(CreateProjectActions.SetTotalAreaSelection(area));
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadArea;
