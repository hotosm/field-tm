import React, { useRef, useState } from 'react';
import Button from '../../components/common/Button';
import { useDispatch } from 'react-redux';
import { CommonActions } from '../../store/slices/CommonSlice';
import RadioButton from '../../components/common/RadioButton';
import AssetModules from '../../shared/AssetModules.js';
import { useNavigate } from 'react-router-dom';

const dataExtractOptions = [
  { name: 'data_extract', value: 'osm_data_extract', label: 'Use OSM data extract' },
  { name: 'data_extract', value: 'custom_data_extract', label: 'Upload custom data extract' },
];

const osmFeatureTypeOptions = [
  { name: 'osm_feature_type', value: 'point_centroid', label: 'Point/Centroid' },
  { name: 'osm_feature_type', value: 'line', label: 'Line' },
  { name: 'osm_feature_type', value: 'polygon', label: 'Polygon' },
];

const DataExtract = ({ flag }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [extractOption, setExtractOption] = useState({});

  const toggleStep = (step, url) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };

  const [selectedFileName, setSelectedFileName] = useState('');

  const changeFileHandler = (event) => {
    const { files } = event.target;
    setSelectedFileName(files[0].name);
  };
  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Data Extract</h6>
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
                topic="You may choose to use OSM data or upload your own data extract"
                options={dataExtractOptions}
                direction="column"
                onChangeData={(value) => setExtractOption(value)}
              />
              {extractOption === 'osm_data_extract' && (
                <div className="fmtm-mt-6">
                  <RadioButton
                    topic="Select OSM feature type"
                    options={osmFeatureTypeOptions}
                    direction="column"
                    onChangeData={(value) => console.log(value)}
                  />
                </div>
              )}
              {extractOption === 'custom_data_extract' && (
                <div className="fmtm-mt-6 fmtm-pb-3">
                  <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
                    <div
                      role="button"
                      onClick={() => fileInputRef?.current?.click()}
                      className="fmtm-bg-primaryRed fmtm-px-4 fmtm-py-1 fmtm-text-white fmtm-rounded-md"
                    >
                      <label id="file-input">
                        <p>Select a file</p>
                        <input ref={fileInputRef} type="file" className="fmtm-hidden" onChange={changeFileHandler} />
                      </label>
                    </div>
                    <div className="fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-slate-100 fmtm-duration-300 fmtm-cursor-pointer">
                      <AssetModules.ReplayIcon className="fmtm-text-gray-600" onClick={() => setSelectedFileName('')} />
                    </div>
                  </div>
                  {selectedFileName && (
                    <div className="fmtm-mt-2">
                      <p>{selectedFileName}</p>
                    </div>
                  )}
                  <p className="fmtm-text-gray-700 fmtm-mt-10">
                    *The supported file formats are zipped shapefile, geojson or kml files.
                  </p>
                </div>
              )}
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => toggleStep(2, '/upload-area')}
                className="fmtm-font-bold"
              />
              <Button
                btnText="NEXT"
                btnType="primary"
                type="button"
                onClick={() => toggleStep(4, '/define-tasks')}
                className="fmtm-font-bold"
              />
            </div>
          </div>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full"></div>
        </div>
      </div>
    </div>
  );
};

export default DataExtract;
