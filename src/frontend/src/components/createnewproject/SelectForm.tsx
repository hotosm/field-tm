import React, { useEffect, useRef, useState } from 'react';
import { useDispatch } from 'react-redux';
import { CommonActions } from '@/store/slices/CommonSlice';
import Button from '@/components/common/Button';
import { CustomSelect } from '@/components/common/Select';
import { useNavigate } from 'react-router-dom';
import RadioButton from '@/components/common/RadioButton';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import { useAppSelector } from '@/types/reduxTypes';
import FileInputComponent from '@/components/common/FileInputComponent';
import SelectFormValidation from '@/components/createnewproject/validation/SelectFormValidation';
import { FormCategoryService, ValidateCustomForm } from '@/api/CreateProjectService';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';

const osmFeatureTypeOptions = [
  { name: 'form_ways', value: 'existing_form', label: 'Use Existing Form' },
  { name: 'form_ways', value: 'custom_form', label: 'Upload a Custom Form' },
];

const SelectForm = ({ flag, geojsonFile, customFormFile, setCustomFormFile }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const dataExtractGeojson = useAppSelector((state) => state.createproject.dataExtractGeojson);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 4 }));
    navigate('/data-extract');
  };
  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, SelectFormValidation);
  const formCategoryList = useAppSelector((state) => state.createproject.formCategoryList);
  const sortedFormCategoryList = formCategoryList.slice().sort((a, b) => a.title.localeCompare(b.title));

  /**
   * Function to handle the change event of a file input.
   *
   * @param {Event} event - The change event object.
   */
  const changeFileHandler = (event): void => {
    // Get the selected files from the event target
    const { files } = event.target;
    // Set the selected file as the customFormFile state
    setCustomFormFile(files[0]);
    handleCustomChange('customFormUpload', files[0]);
  };
  const resetFile = (): void => {
    setCustomFormFile(null);
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

  const toggleStep = (step, url) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };
  useEffect(() => {
    if (customFormFile) {
      dispatch(ValidateCustomForm(`${import.meta.env.VITE_API_URL}/projects/validate_form`, customFormFile));
    }
  }, [customFormFile]);
  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Select Category</h6>
        <p className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>You may choose an existing category or upload a custom XLS form.</span>
          <span>
            {' '}
            You may learn more about XLSforms{' '}
            <a
              href="https://hotosm.github.io/osm-fieldwork/about/xlsforms/"
              target="_"
              className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
            >
              here
            </a>
            .
          </span>{' '}
        </p>
      </div>
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] lg:fmtm-h-[60vh] xl:fmtm-h-[58vh] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <form onSubmit={handleSubmit} className="fmtm-flex fmtm-flex-col lg:fmtm-w-[40%] fmtm-justify-between">
            <div className="fmtm-flex fmtm-flex-col  fmtm-gap-6">
              <div className="">
                <CustomSelect
                  title="Select category"
                  placeholder="Select category"
                  data={sortedFormCategoryList}
                  dataKey="id"
                  valueKey="title"
                  label="title"
                  value={formValues.formCategorySelection}
                  onValueChange={(value) => {
                    handleCustomChange('formCategorySelection', value);
                    dispatch(CreateProjectActions.setDataExtractGeojson(null));
                  }}
                  errorMsg={errors.formCategorySelection}
                  className="fmtm-max-w-[13.5rem]"
                />
                <p className="fmtm-text-base fmtm-mt-2">
                  You will view the OSM data extracts of{' '}
                  <a
                    href="https://wiki.openstreetmap.org/wiki/Tags"
                    target="_"
                    className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
                  >
                    tags
                  </a>{' '}
                  {`that match the selected category in OSM database, if you don't choose to upload custom data extract.`}
                </p>
              </div>
              <RadioButton
                topic="You may choose to use existing category or upload your own xlsx form"
                options={osmFeatureTypeOptions}
                direction="column"
                value={formValues.formWays}
                onChangeData={(value) => {
                  handleCustomChange('formWays', value);
                }}
                errorMsg={errors.formWays}
              />
              {formValues.formWays === 'custom_form' ? (
                <FileInputComponent
                  onChange={changeFileHandler}
                  onResetFile={resetFile}
                  customFile={customFormFile}
                  btnText="Select a Form"
                  accept=".xls,.xlsx"
                  fileDescription="*The supported file formats are .xlsx, .xls"
                  errorMsg={errors.customFormUpload}
                />
              ) : null}
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
                type="submit"
                onClick={() => console.log('submit')}
                className="fmtm-font-bold"
              />
            </div>
          </form>
          <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full">
            <NewDefineAreaMap uploadedOrDrawnGeojsonFile={drawnGeojson} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SelectForm;
