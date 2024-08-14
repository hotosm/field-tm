import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { CommonActions } from '@/store/slices/CommonSlice';
import Button from '@/components/common/Button';
import { CustomSelect } from '@/components/common/Select';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import { useAppSelector } from '@/types/reduxTypes';
import FileInputComponent from '@/components/common/FileInputComponent';
import SelectFormValidation from '@/components/createnewproject/validation/SelectFormValidation';
import { FormCategoryService, ValidateCustomForm } from '@/api/CreateProjectService';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import { CustomCheckbox } from '../common/Checkbox';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const SelectForm = ({ flag, geojsonFile, customFormFile, setCustomFormFile }) => {
  useDocumentTitle('Create Project: Select Category');
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const dataExtractGeojson = useAppSelector((state) => state.createproject.dataExtractGeojson);
  const customFileValidity = useAppSelector((state) => state.createproject.customFileValidity);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    if (!customFileValidity && formValues.formWays === 'custom_form') {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'Your file is invalid',
          variant: 'error',
          duration: 2000,
        }),
      );
      return;
    }
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 4 }));
    navigate('/map-features');
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
    dispatch(CreateProjectActions.SetCustomFileValidity(false));
    // Get the selected files from the event target
    const { files } = event.target;
    // Set the selected file as the customFormFile state
    setCustomFormFile(files[0]);
    handleCustomChange('customFormUpload', files[0]);
  };
  const resetFile = (): void => {
    handleCustomChange('customFormUpload', null);
    dispatch(CreateProjectActions.SetCustomFileValidity(false));
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
    if (customFormFile && !customFileValidity) {
      dispatch(ValidateCustomForm(`${import.meta.env.VITE_API_URL}/projects/validate-form`, customFormFile));
    }
  }, [customFormFile]);
  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6 lg:fmtm-h-full lg:fmtm-overflow-y-scroll lg:scrollbar">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Select Category</h6>
        <p className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>
            You may choose a pre-configured form, or upload a custom XLS form. Click{' '}
            <a
              href="https://hotosm.github.io/osm-fieldwork/about/xlsforms/"
              target="_"
              className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer"
            >
              here
            </a>{' '}
            to learn more about XLSForm building.{' '}
          </span>
          <span>
            For creating a custom XLS form, there are few essential fields that must be present for FMTM to function.
            You may either download the sample XLS file and modify all fields that are not hidden, or edit the sample
            form interactively in the browser.
          </span>
        </p>
      </div>
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 fmtm-h-full lg:fmtm-overflow-y-scroll lg:scrollbar">
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
                  The category will be used to set the OpenStreetMap{' '}
                  <a
                    href="https://wiki.openstreetmap.org/wiki/Tags"
                    target="_"
                    className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
                  >
                    tags
                  </a>{' '}
                  {`if uploading the final submissions to OSM.`}
                </p>
              </div>
              <CustomCheckbox
                key="uploadCustomXForm"
                label="Upload a custom XLSForm instead"
                checked={formValues.formWays === 'custom_form'}
                onCheckedChange={(status) => {
                  if (status) {
                    handleCustomChange('formWays', 'custom_form');
                  } else {
                    handleCustomChange('formWays', 'existing_form');
                  }
                }}
                className="fmtm-text-black"
                labelClickable
                disabled={!formValues.formCategorySelection}
              />
              {formValues.formWays === 'custom_form' ? (
                <div>
                  <p className="fmtm-text-base fmtm-mt-2">
                    Please extend upon the existing XLSForm for the selected category:
                  </p>
                  <p className="fmtm-text-base fmtm-mt-2">
                    <a
                      href={`${import.meta.env.VITE_API_URL}/helper/download-template-xlsform?category=${
                        formValues.formCategorySelection
                      }`}
                      target="_"
                      className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
                    >
                      Download Form
                    </a>
                  </p>
                  <p className="fmtm-text-base fmtm-mt-2">
                    <a
                      href={`https://xlsforms.fmtm.dev/?url=${
                        import.meta.env.VITE_API_URL
                      }/helper/download-template-xlsform?category=${formValues.formCategorySelection}`}
                      target="_"
                      className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
                    >
                      Edit Interactively
                    </a>
                  </p>
                  <FileInputComponent
                    onChange={changeFileHandler}
                    onResetFile={resetFile}
                    customFile={customFormFile}
                    btnText="Select a Form"
                    accept=".xls,.xlsx,.xml"
                    fileDescription="*The supported file formats are .xlsx, .xls, .xml"
                    errorMsg={errors.customFormUpload}
                  />
                </div>
              ) : null}
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                btnText="PREVIOUS"
                btnType="secondary"
                type="button"
                onClick={() => {
                  dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
                  toggleStep(2, '/upload-area');
                }}
                className="fmtm-font-bold"
              />
              <Button btnText="NEXT" btnType="primary" type="submit" className="fmtm-font-bold" />
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
