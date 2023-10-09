import React, { useEffect, useRef, useState } from 'react';
import enviroment from '../../environment';
import { FormCategoryService } from '../../api/CreateProjectService';
import CoreModules from '../../shared/CoreModules.js';
import Button from '../../components/common/Button';
import { useDispatch } from 'react-redux';
import { CommonActions } from '../../store/slices/CommonSlice';
import RadioButton from '../../components/common/RadioButton';
import { useNavigate } from 'react-router-dom';
import { CustomSelect } from '../../components/common/Select';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import useForm from '../../hooks/useForm';
import { useAppSelector } from '../../types/reduxTypes';
import DataExtractValidation from './validation/DataExtractValidation';
import FileInputComponent from '../../components/common/FileInputComponent';

const dataExtractOptions = [
  { name: 'data_extract', value: 'osm_data_extract', label: 'Use OSM data extract' },
  { name: 'data_extract', value: 'custom_data_extract', label: 'Upload custom data extract' },
];

const osmFeatureTypeOptions = [
  { name: 'osm_feature_type', value: 'point_centroid', label: 'Point/Centroid' },
  { name: 'osm_feature_type', value: 'line', label: 'Line' },
  { name: 'osm_feature_type', value: 'polygon', label: 'Polygon' },
];

const DataExtract = ({ flag, customFormFile, setCustomFormFile }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const customFileRef: any = useRef();

  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const formCategoryList = CoreModules.useAppSelector((state) => state.createproject.formCategoryList);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 3 }));
    navigate('/new-upload-area');
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
  const changeFileHandler = (event) => {
    const { files } = event.target;
    setCustomFormFile(files[0]);
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

  const resetFile = () => {
    customFileRef.current.value = '';
    setCustomFormFile(null);
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

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
                  />
                </div>
              )}
              {formValues.dataExtractWays === 'custom_data_extract' && (
                <>
                  <FileInputComponent
                    customFileRef={customFileRef}
                    onChange={changeFileHandler}
                    onResetFile={resetFile}
                    customFormFile={customFormFile}
                  />
                  <FileInputComponent
                    customFileRef={customFileRef}
                    onChange={changeFileHandler}
                    onResetFile={resetFile}
                    customFormFile={customFormFile}
                  />
                </>
              )}
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => toggleStep(2, '/new-upload-area')}
                className="fmtm-font-bold"
              />
              <Button btnText="NEXT" btnType="primary" type="submit" className="fmtm-font-bold" />
            </div>
          </form>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full"></div>
        </div>
      </div>
    </div>
  );
};

export default DataExtract;
