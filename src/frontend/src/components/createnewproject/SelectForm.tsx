import React, { useEffect } from 'react';
import { CommonActions } from '@/store/slices/CommonSlice';
import Button from '@/components/common/Button';
import { CustomSelect } from '@/components/common/Select';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import SelectFormValidation from '@/components/createnewproject/validation/SelectFormValidation';
import { FormCategoryService, ValidateCustomForm } from '@/api/CreateProjectService';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { Loader2 } from 'lucide-react';
import DescriptionSection from '@/components/createnewproject/Description';
import { osm_forms } from '@/types/enums';
import UploadArea from '@/components/common/UploadArea';
import { Tooltip } from '@mui/material';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const SelectForm = ({ flag, _geojsonFile, xlsFormFile, setXlsFormFile }) => {
  useDocumentTitle('Create Project: Upload Survey');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const customFileValidity = useAppSelector((state) => state.createproject.customFileValidity);
  const validateCustomFormLoading = useAppSelector((state) => state.createproject.validateCustomFormLoading);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    if (!customFileValidity) {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'Your file is invalid',
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
  const formExampleList = useAppSelector((state) => state.createproject.formExampleList);
  const sortedFormExampleList = formExampleList.slice().sort((a, b) => a.title.localeCompare(b.title));

  /**
   * Function to handle the change event of a file input.
   *
   * @param {Event} event - The change event object.
   */
  const changeFileHandler = (file): void => {
    if (!file) {
      resetFile();
      return;
    }
    dispatch(CreateProjectActions.SetCustomFileValidity(false));
    // Set the selected file as the xlsFormFile state
    setXlsFormFile(file);
    handleCustomChange('xlsFormFileUpload', file);
  };

  const resetFile = (): void => {
    handleCustomChange('xlsFormFileUpload', null);
    dispatch(CreateProjectActions.SetCustomFileValidity(false));
    setXlsFormFile(null);
  };

  useEffect(() => {
    dispatch(FormCategoryService(`${VITE_API_URL}/central/list-forms`));
  }, []);

  const toggleStep = (step, url) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
  };

  useEffect(() => {
    if (xlsFormFile && !customFileValidity) {
      dispatch(ValidateCustomForm(`${VITE_API_URL}/projects/validate-form`, xlsFormFile?.file));
    }
  }, [xlsFormFile]);

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
      <DescriptionSection section="Upload Survey" />
      <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 fmtm-h-full lg:fmtm-overflow-y-scroll lg:scrollbar">
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
          <form onSubmit={handleSubmit} className="fmtm-flex fmtm-flex-col lg:fmtm-w-[40%] fmtm-justify-between">
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-3">
              <div
                onMouseOver={() => {
                  dispatch(CreateProjectActions.SetDescriptionToFocus('selectform-selectform'));
                }}
                onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
              >
                <div className="fmtm-flex fmtm-gap-1">
                  <p className="fmtm-text-[1rem] fmtm-mb-1 fmtm-font-semibold !fmtm-bg-transparent">
                    What are you surveying?
                  </p>
                  <p className="fmtm-text-red-500 fmtm-text-[1.2rem]">*</p>
                </div>
                <UploadArea
                  title="Upload Form"
                  label="The supported file formats are .xlsx, .xls, .xml"
                  data={xlsFormFile ? [xlsFormFile] : []}
                  onUploadFile={(updatedFiles) => {
                    changeFileHandler(updatedFiles?.[0]);
                  }}
                  acceptedInput=".xls,.xlsx,.xml"
                />
                {!xlsFormFile && (
                  <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.xlsFormFileUpload}</p>
                )}
              </div>
              {validateCustomFormLoading && (
                <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
                  <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-primaryRed" />
                  <p className="fmtm-text-base">Validating form...</p>
                </div>
              )}
              <div>
                <CustomSelect
                  title="Browse available forms"
                  placeholder="Example Forms"
                  data={sortedFormExampleList}
                  dataKey="id"
                  valueKey="title"
                  label="title"
                  value={formValues.formExampleSelection}
                  onValueChange={(value) => {
                    handleCustomChange('formExampleSelection', value);
                    // Only set osmFormSelectionName for specific 'OSM forms'
                    if (Object.values(osm_forms).includes(value as osm_forms)) {
                      handleCustomChange('osmFormSelectionName', value);
                    }
                    dispatch(CreateProjectActions.setDataExtractGeojson(null));
                  }}
                  errorMsg={errors.formExampleSelection}
                  className="fmtm-max-w-[13.5rem]"
                />
                <p className="fmtm-text-base fmtm-mt-2">
                  Selecting a form based on OpenStreetMap{' '}
                  <a
                    href="https://wiki.openstreetmap.org/wiki/Tags"
                    target="_"
                    className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
                  >
                    tags
                  </a>{' '}
                  {`will help with merging the final data back to OSM.`}
                </p>
                <p className="fmtm-text-base fmtm-mt-2">
                  <Tooltip
                    arrow
                    placement="bottom"
                    title={!formValues.formExampleSelection ? 'Please select a form category first' : ''}
                  >
                    <div className="fmtm-w-fit">
                      <a
                        href={`${VITE_API_URL}/helper/download-template-xlsform?form_type=${formValues.formExampleSelection}`}
                        target="_"
                        className={`fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline fmtm-w-fit ${!formValues.formExampleSelection && 'fmtm-opacity-70 fmtm-pointer-events-none'}`}
                      >
                        Download Form
                      </a>
                    </div>
                  </Tooltip>
                </p>
                <p className="fmtm-text-base fmtm-mt-2">
                  <a
                    href={`https://xlsforms.fmtm.dev?url=${VITE_API_URL}/helper/download-template-xlsform?form_type=${formValues.formExampleSelection}`}
                    target="_"
                    className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
                  >
                    Edit Interactively
                  </a>
                </p>
              </div>
            </div>
            <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
              <Button
                variant="secondary-grey"
                onClick={() => {
                  dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
                  toggleStep(2, '/project-area');
                }}
              >
                PREVIOUS
              </Button>
              <Button variant="primary-red" type="submit" disabled={validateCustomFormLoading}>
                NEXT
              </Button>
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
