import TextArea from '@/components/common/TextArea';
import InputTextField from '@/components/common/InputTextField';
import React, { useEffect, useState } from 'react';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import useForm from '@/hooks/useForm';
import CreateProjectValidation from '@/components/createnewproject/validation/CreateProjectValidation';
import Button from '@/components/common/Button';
import { CommonActions } from '@/store/slices/CommonSlice';
import { OrganisationService } from '@/api/CreateProjectService';
import { CustomCheckbox } from '@/components/common/Checkbox';
import RichTextEditor from '@/components/common/Editor/Editor';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import DescriptionSection from '@/components/createnewproject/Description';
import Select2 from '@/components/common/Select2';
import { GetUserListService } from '@/api/User';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const ProjectDetailsForm = ({ flag }) => {
  useDocumentTitle('Create Project: Project Details');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const organisationListData = useAppSelector((state) => state.createproject.organisationList);
  const organisationListLoading = useAppSelector((state) => state.createproject.organisationListLoading);
  const userList = useAppSelector((state) => state.user.userList)?.map((user) => ({
    id: user.id,
    label: user.username,
    value: user.id,
  }));
  const userListLoading = useAppSelector((state) => state.user.userListLoading);

  const organisationList = organisationListData.map((item) => ({
    id: item.id,
    label: item.name,
    value: item.id,
    hasODKCredentials: item?.odk_central_url ? true : false,
  }));
  const [hasODKCredentials, setHasODKCredentials] = useState(false);

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(values));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 2 }));
    navigate('/project-area');
  };

  const { handleSubmit, handleChange, handleCustomChange, values, errors }: any = useForm(
    projectDetails,
    submission,
    CreateProjectValidation,
  );

  const onFocus = () => {
    dispatch(OrganisationService(`${VITE_API_URL}/organisation`));
  };

  useEffect(() => {
    window.addEventListener('focus', onFocus);
    onFocus();
    // Calls onFocus when the window first loads
    return () => {
      window.removeEventListener('focus', onFocus);
    };
  }, []);

  useEffect(() => {
    dispatch(GetUserListService(`${VITE_API_URL}/users`));
  }, []);

  const handleInputChanges = (e) => {
    handleChange(e);
    dispatch(CreateProjectActions.SetIsUnsavedChanges(true));
  };

  const getSelectedOrganization = () => {
    return organisationList.find((org) => org.value === values.organisation_id);
  };

  const handleOrganizationChange = (orgId: number) => {
    // Ensure orgId is not null or undefined before integer convert
    const orgIdInt = orgId && +orgId;

    if (!orgIdInt) {
      return;
    }

    const selectedOrg = organisationList.find((org) => org.value === orgIdInt);
    handleCustomChange('organisation_id', orgIdInt);
    handleCustomChange('useDefaultODKCredentials', selectedOrg?.hasODKCredentials || false);
  };

  useEffect(() => {
    if (!values.organisation_id) {
      handleCustomChange('useDefaultODKCredentials', false);
    }
  }, []);

  useEffect(() => {
    if (values.useDefaultODKCredentials) {
      // Reset user provided credentials
      handleCustomChange('odk_central_url', '');
      handleCustomChange('odk_central_user', '');
      handleCustomChange('odk_central_password', '');
    }
  }, [values.useDefaultODKCredentials]);

  useEffect(() => {
    organisationList?.map((organization) => {
      if (values?.organisation_id == organization?.value) {
        setHasODKCredentials(organization.hasODKCredentials);
      }
    });
  }, [organisationList]);

  const shouldShowCustomODKFields = () => {
    const currentOrg = getSelectedOrganization();
    return !values.useDefaultODKCredentials || !currentOrg?.hasODKCredentials;
  };

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
      <DescriptionSection section="Project Details" />
      <form
        className="xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-h-full fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar"
        onSubmit={handleSubmit}
      >
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 xl:fmtm-w-[50%]">
          {/* Project name & descriptions */}
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
          {/* Select organisation */}
          <div>
            <p className={`fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold !fmtm-bg-transparent`}>
              Organization Name <span className="fmtm-text-red-500 fmtm-text-[1rem]">*</span>
            </p>
            <Select2
              options={organisationList || []}
              value={values.organisation_id}
              onChange={(value: any) => {
                handleOrganizationChange(value);
              }}
              placeholder="Organization Name"
              className="naxatw-w-1/5 naxatw-min-w-[9rem]"
              isLoading={organisationListLoading}
            />
            {errors.organisation_id && (
              <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.organisation_id}</p>
            )}
          </div>
          {/* Select project admin */}
          <div>
            <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold !fmtm-bg-transparent">Assign Project Admin</p>
            <Select2
              options={userList || []}
              value={values.project_admins}
              onChange={(value: any) => {
                handleCustomChange('project_admins', value);
              }}
              placeholder="Assign Project Admin"
              className="naxatw-w-1/5 naxatw-min-w-[9rem]"
              multiple
              checkBox
              isLoading={userListLoading}
            />
          </div>
          {/* Custom ODK creds toggle */}
          <div
            className="fmtm-flex fmtm-flex-col fmtm-gap-6"
            onMouseOver={() => {
              dispatch(CreateProjectActions.SetDescriptionToFocus('projectdetails-odk'));
            }}
            onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
          >
            {
              <CustomCheckbox
                key="useDefaultODKCredentials"
                label="Use default ODK credentials"
                checked={values.useDefaultODKCredentials}
                onCheckedChange={() => {
                  handleCustomChange('useDefaultODKCredentials', !values.useDefaultODKCredentials);
                }}
                className="fmtm-text-black"
                labelClickable={hasODKCredentials} // Dynamically set labelClickable based on hasODKCredentials
              />
            }
            {shouldShowCustomODKFields() && (
              <ODKCredentialsFields values={values} errors={errors} handleChange={handleChange} />
            )}
          </div>
          {/* Hashtags */}
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
          {/* Custom TMS */}
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-5">
            <div
              onMouseOver={() => {
                dispatch(CreateProjectActions.SetDescriptionToFocus('projectdetails-tms'));
              }}
              onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
            >
              <CustomCheckbox
                key="hasCustomTMS"
                label="I would like to include my own imagery layer for reference"
                checked={values.hasCustomTMS}
                onCheckedChange={() => {
                  handleCustomChange('hasCustomTMS', !values.hasCustomTMS);
                }}
                className="fmtm-text-black"
              />
            </div>
            {values.hasCustomTMS && (
              <InputTextField
                id="custom_tms_url"
                name="custom_tms_url"
                label="Please specify the TMS URL"
                value={values?.custom_tms_url}
                onChange={handleChange}
                fieldType="text"
                errorMsg={errors.custom_tms_url}
              />
            )}
          </div>
          {/* Task instructions */}
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

const ODKCredentialsFields = ({ values, errors, handleChange }) => (
  <>
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
  </>
);

export default ProjectDetailsForm;
