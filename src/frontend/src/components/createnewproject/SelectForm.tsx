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
import { Loader2 } from 'lucide-react';
import DescriptionSection from '@/components/createnewproject/Description';

const SelectForm = ({ flag, geojsonFile, customFormFile, setCustomFormFile }) => {
  useDocumentTitle('Create Project: Upload Survey');
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const customFileValidity = useAppSelector((state) => state.createproject.customFileValidity);
  const validateCustomFormLoading = useAppSelector((state) => state.createproject.validateCustomFormLoading);

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
    navigate('/map-data');
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
      <DescriptionSection section="Upload Survey" />
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 fmtm-h-full lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <form onSubmit={handleSubmit} className="fmtm-flex fmtm-flex-col lg:fmtm-w-[40%] fmtm-justify-between">
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
              <div className="">
                <CustomSelect
                  title="What are you Surveying"
                  placeholder="Survey Type"
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
                  The survey type will be used to set the OpenStreetMap{' '}
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
              <div
                onMouseOver={() => {
                  dispatch(CreateProjectActions.SetDescriptionToFocus('selectform-customform'));
                }}
                onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
              >
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
              </div>
              {formValues.formWays === 'custom_form' ? (
                <div>
                  <div
                    onMouseOver={() => {
                      dispatch(CreateProjectActions.SetDescriptionToFocus('selectform-customform'));
                    }}
                    onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
                  >
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
                        href={`https://xlsforms.fmtm.dev?url=${
                          import.meta.env.VITE_API_URL
                        }/helper/download-template-xlsform?category=${formValues.formCategorySelection}`}
                        target="_"
                        className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
                      >
                        Edit Interactively
                      </a>
                    </p>
                  </div>
                  <div
                    onMouseOver={() => {
                      dispatch(CreateProjectActions.SetDescriptionToFocus('selectform-selectform'));
                    }}
                    onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
                  >
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
                  {validateCustomFormLoading && (
                    <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mt-2">
                      <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-primaryRed" />
                      <p className="fmtm-text-base">Validating form...</p>
                    </div>
                  )}
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
                  toggleStep(2, '/project-area');
                }}
                className="fmtm-font-bold"
              />
              <Button
                btnText="NEXT"
                btnType="primary"
                type="submit"
                className="fmtm-font-bold"
                disabled={validateCustomFormLoading}
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
