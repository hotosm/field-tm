import TextArea from '@/components/common/TextArea';
import InputTextField from '@/components/common/InputTextField';
import React, { useEffect } from 'react';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import useForm from '@/hooks/useForm';
import CreateProjectValidation from '@/components/createnewproject/validation/CreateProjectValidation';
import Button from '@/components/common/Button';
import { CommonActions } from '@/store/slices/CommonSlice';
import AssetModules from '@/shared/AssetModules.js';
import { createPopup } from '@/utilfunctions/createPopup';
import { CustomSelect } from '@/components/common/Select';
import { OrganisationService } from '@/api/CreateProjectService';

const ProjectDetailsForm = ({ flag }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const organisationListData: any = useAppSelector((state) => state.createproject.organisationList);

  const organisationList = organisationListData.map((item) => ({ label: item.name, value: item.id }));

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(values));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 2 }));
    navigate('/upload-area');
  };

  const { handleSubmit, handleChange, handleCustomChange, values, errors, checkValidationOnly }: any = useForm(
    projectDetails,
    submission,
    CreateProjectValidation,
  );

  const onFocus = () => {
    dispatch(OrganisationService(`${import.meta.env.VITE_API_URL}/organisation/`));
  };

  useEffect(() => {
    window.addEventListener('focus', onFocus);
    onFocus();
    // Calls onFocus when the window first loads
    return () => {
      window.removeEventListener('focus', onFocus);
      // dispatch(
      //   CreateProjectActions.SetCreateProjectValidations({ key: 'projectDetails', value: checkValidationOnly() }),
      // );
    };
  }, []);

  const hashtagPrefix = '#FMTM ';

  // Checks if hashtag value starts with hotosm-fmtm'
  const handleHashtagOnChange = (e) => {
    let enteredText = e.target.value;
    if (!enteredText.startsWith(hashtagPrefix)) {
      handleCustomChange('hashtags', hashtagPrefix);
      return;
    }
    handleCustomChange('hashtags', enteredText);
  };

  // Doesn't let the user to press 'Backspace' or 'Delete' if input value is 'hotosm-fmtm '
  const handleHashtagKeyPress = (e) => {
    if (
      ((e.key === 'Backspace' || e.key === 'Delete') && values.hashtags === hashtagPrefix) ||
      (e.ctrlKey && e.key === 'Backspace')
    ) {
      e.preventDefault();
    }
  };
  const handleInputChanges = (e) => {
    handleChange(e);
    dispatch(CreateProjectActions.SetIsUnsavedChanges(true));
  };

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row">
      <div className="fmtm-bg-white xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Project Details</h6>
        <div className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>
            Fill in your project basic information such as name, description, hashtag, etc. This captures essential
            information about your project.
          </span>
          <span>To complete the first step, you will need the login credentials of ODK Central Server.</span>{' '}
          <div>
            <a
              href="https://docs.getodk.org/central-install-digital-ocean/"
              className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              Here{' '}
            </a>
            <span>
              are the instructions for setting up a Central ODK Server on Digital Ocean, if you haven’t already.
            </span>
          </div>
        </div>
      </div>
      <form
        className="xl:fmtm-w-[83%] lg:fmtm-h-[60vh] xl:fmtm-h-[58vh] fmtm-bg-white fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar"
        onSubmit={handleSubmit}
      >
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 md:fmtm-w-[50%]">
            <InputTextField
              id="name"
              name="name"
              label="Project Name"
              value={values?.name}
              onChange={handleInputChanges}
              fieldType="text"
              required
              errorMsg={errors.name}
            />
            <TextArea
              id="short_description"
              name="short_description"
              label="Short Description"
              rows={3}
              value={values?.short_description}
              onChange={handleInputChanges}
              required
              errorMsg={errors.short_description}
            />
            <InputTextField
              id="odk_central_url"
              name="odk_central_url"
              label="ODK Central URL"
              value={values?.odk_central_url}
              onChange={handleChange}
              fieldType="text"
              required
              errorMsg={errors.odk_central_url}
            />
            <InputTextField
              id="odk_central_user"
              name="odk_central_user"
              label="Central ODK Email/Username"
              value={values?.odk_central_user}
              onChange={handleChange}
              fieldType="text"
              required
              errorMsg={errors.odk_central_user}
            />
            <InputTextField
              id="odk_central_password"
              name="odk_central_password"
              label="Central ODK Password"
              value={values?.odk_central_password}
              onChange={handleChange}
              fieldType="password"
              required
              errorMsg={errors.odk_central_password}
            />
            <div>
              <InputTextField
                id="hashtags"
                label="Changeset Comment"
                value={values?.hashtags}
                onChange={(e) => {
                  handleHashtagOnChange(e);
                }}
                onKeyDown={(e) => {
                  handleHashtagKeyPress(e);
                }}
                fieldType="text"
                required
                errorMsg={errors.hashtag}
              />
              <p className="fmtm-text-sm fmtm-text-gray-500 fmtm-leading-4 fmtm-mt-2">
                *Default comments added to uploaded changeset comment field. Users should also be encouraged to add text
                describing what they mapped. Hashtags are sometimes used for analysis later, but should be human
                informative and not overused, #group #event
              </p>
            </div>
          </div>
          <div className="md:fmtm-w-[50%] fmtm-flex fmtm-flex-col fmtm-gap-6">
            <div className="">
              <div className="fmtm-flex fmtm-items-center fmtm-max-w-[18rem]">
                <CustomSelect
                  title="Organization Name"
                  placeholder="Organization Name"
                  data={organisationList}
                  dataKey="value"
                  value={values.organisation_id?.toString()}
                  valueKey="value"
                  label="label"
                  onValueChange={(value) => handleCustomChange('organisation_id', value && +value)}
                />
                <AssetModules.AddIcon
                  className="fmtm-bg-red-600 fmtm-text-white fmtm-rounded-full fmtm-mb-[0.15rem] hover:fmtm-bg-red-700 hover:fmtm-cursor-pointer fmtm-ml-5 fmtm-mt-9"
                  onClick={() => createPopup('Create Organization', 'createOrganisation?popup=true')}
                />
              </div>
              {errors.organisation_id && (
                <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.organisation_id}</p>
              )}
            </div>
            <TextArea
              id="description"
              label="Description"
              rows={3}
              value={values?.description}
              onChange={(e) => handleCustomChange('description', e.target.value)}
              required
              errorMsg={errors.description}
            />
          </div>
        </div>
        <div className="fmtm-w-fit fmtm-mx-auto fmtm-mt-10">
          <Button btnText="NEXT" btnType="primary" type="submit" className="fmtm-font-bold" />
        </div>
      </form>
    </div>
  );
};

export default ProjectDetailsForm;
