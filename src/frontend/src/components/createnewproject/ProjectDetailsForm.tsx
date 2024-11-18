import TextArea from '@/components/common/TextArea';
import InputTextField from '@/components/common/InputTextField';
import React, { useEffect, useState } from 'react';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import useForm from '@/hooks/useForm';
import CreateProjectValidation from '@/components/createnewproject/validation/CreateProjectValidation';
import Button from '@/components/common/Button';
import { CommonActions } from '@/store/slices/CommonSlice';
import { CustomSelect } from '@/components/common/Select';
import { OrganisationService } from '@/api/CreateProjectService';
import { CustomCheckbox } from '@/components/common/Checkbox';
import { organizationDropdownType } from '@/models/createproject/createProjectModel';
import RichTextEditor from '@/components/common/Editor/Editor';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const ProjectDetailsForm = ({ flag }) => {
  useDocumentTitle('Create Project: Project Details');
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const organisationListData = useAppSelector((state) => state.createproject.organisationList);
  const organisationList: organizationDropdownType[] = organisationListData.map((item) => ({
    label: item.name,
    value: item.id,
    hasODKCredentials: item?.odk_central_url ? true : false,
  }));
  const [hasODKCredentials, setHasODKCredentials] = useState(false);

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
    dispatch(OrganisationService(`${import.meta.env.VITE_API_URL}/organisation`));
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

  const handleInputChanges = (e) => {
    handleChange(e);
    dispatch(CreateProjectActions.SetIsUnsavedChanges(true));
  };

  const setSelectedOrganisation = (orgId) => {
    // Ensure orgId is not null or undefined before integer convert
    const orgIdInt = orgId && +orgId;

    if (!orgIdInt) {
      return;
    }

    handleCustomChange('organisation_id', orgIdInt);

    const selectedOrg = organisationList.find((org) => org.value === orgIdInt);

    if (selectedOrg && selectedOrg.hasODKCredentials) {
      handleCustomChange('defaultODKCredentials', selectedOrg.hasODKCredentials);
    }
  };

  useEffect(() => {
    if (!values.organisation_id) {
      handleCustomChange('defaultODKCredentials', false);
    }
  }, []);

  useEffect(() => {
    if (values.defaultODKCredentials) {
      // Reset user provided credentials
      handleCustomChange('odk_central_url', '');
      handleCustomChange('odk_central_user', '');
      handleCustomChange('odk_central_password', '');
    }
  }, [values.defaultODKCredentials]);

  useEffect(() => {
    organisationList?.map((organization) => {
      if (values?.organisation_id == organization?.value) {
        setHasODKCredentials(organization.hasODKCredentials);
      }
    });
  }, [organisationList]);

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
      <div className="fmtm-bg-white lg:fmtm-w-[20%] xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6 lg:fmtm-h-full lg:fmtm-overflow-y-scroll lg:scrollbar">
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
          <div>
            You can use the 'Custom TMS URL' option to integrate high-resolution aerial imagery like OpenAerialMap{' '}
            <a
              href="https://openaerialmap.org/"
              className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              (OAM)
            </a>
            . Simply obtain the TMS URL and paste it into the custom TMS field. More details:{' '}
            <a
              href="https://docs.openaerialmap.org/"
              className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              OpenAerialMap Documentation
            </a>
            .
          </div>
        </div>
      </div>
      <form
        className="xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-11 fmtm-h-full fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar"
        onSubmit={handleSubmit}
      >
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 xl:fmtm-w-[50%]">
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
            rows={2}
            value={values?.short_description}
            onChange={handleInputChanges}
            required
            errorMsg={errors.short_description}
            maxLength={200}
          />
          <TextArea
            id="description"
            label="Description"
            rows={3}
            value={values?.description}
            onChange={(e) => handleCustomChange('description', e.target.value)}
            required
            errorMsg={errors.description}
          />
          <div className="">
            <div className="fmtm-flex fmtm-items-center">
              <CustomSelect
                title="Organization Name"
                placeholder="Organization Name"
                data={organisationList}
                dataKey="value"
                value={values.organisation_id?.toString()}
                valueKey="value"
                label="label"
                onValueChange={(value) => {
                  setSelectedOrganisation(value);
                }}
                required
              />
            </div>
            {errors.organisation_id && (
              <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.organisation_id}</p>
            )}
          </div>
          {hasODKCredentials && (
            <CustomCheckbox
              key="defaultODKCredentials"
              label="Use default ODK credentials"
              checked={values.defaultODKCredentials}
              onCheckedChange={() => {
                handleCustomChange('defaultODKCredentials', !values.defaultODKCredentials);
              }}
              className="fmtm-text-black"
              labelClickable={true}
            />
          )}
          {((!values.defaultODKCredentials && hasODKCredentials) || !hasODKCredentials) && (
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
              <InputTextField
                id="odk_central_url"
                name="odk_central_url"
                label="ODK Central URL"
                value={values?.odk_central_url}
                onChange={handleChange}
                fieldType="text"
                errorMsg={errors.odk_central_url}
                required
              />
              <InputTextField
                id="odk_central_user"
                name="odk_central_user"
                label="ODK Central Email"
                value={values?.odk_central_user}
                onChange={handleChange}
                fieldType="text"
                errorMsg={errors.odk_central_user}
                required
              />
              <InputTextField
                id="odk_central_password"
                name="odk_central_password"
                label="ODK Central Password"
                value={values?.odk_central_password}
                onChange={handleChange}
                fieldType="password"
                errorMsg={errors.odk_central_password}
                required
              />
            </div>
          )}
          <div>
            <InputTextField
              id="hashtags"
              label="Hashtags"
              value={values?.hashtags}
              onChange={(e) => {
                handleCustomChange('hashtags', e.target.value);
              }}
              fieldType="text"
              errorMsg={errors.hashtag}
            />
            <p className="fmtm-text-sm fmtm-text-gray-500 fmtm-leading-4 fmtm-mt-2">
              *Hashtags related to what is being mapped. By default #FMTM is included. Hashtags are sometimes used for
              analysis later, but should be human informative and not overused, #group #event
            </p>
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-5">
            <CustomCheckbox
              key="hasCustomTMS"
              label="Will you use a custom TMS basemap"
              checked={values.hasCustomTMS}
              onCheckedChange={() => {
                handleCustomChange('hasCustomTMS', !values.hasCustomTMS);
              }}
              className="fmtm-text-black"
            />
            {values.hasCustomTMS && (
              <InputTextField
                id="custom_tms_url"
                name="custom_tms_url"
                label="Custom TMS URL"
                value={values?.custom_tms_url}
                onChange={handleChange}
                fieldType="text"
                errorMsg={errors.custom_tms_url}
              />
            )}
          </div>
          <div>
            <p className="fmtm-text-[1rem] fmtm-font-semibold fmtm-mb-2">Instructions</p>
            <RichTextEditor
              editorHtmlContent={values?.per_task_instructions}
              setEditorHtmlContent={(content) => handleCustomChange('per_task_instructions', content)}
              editable={true}
            />
          </div>
          <div className="fmtm-w-fit fmtm-mx-auto fmtm-mt-10">
            <Button btnText="NEXT" btnType="primary" type="submit" className="fmtm-font-bold" />
          </div>
        </div>
      </form>
    </div>
  );
};

export default ProjectDetailsForm;
