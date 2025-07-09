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
import { GetUserListForSelect } from '@/api/User';
import { UserActions } from '@/store/slices/UserSlice';
import CoreModules from '@/shared/CoreModules';
import { useIsAdmin } from '@/hooks/usePermissions';
import { isEmpty } from '@/utilfunctions/commonUtils';
import AssetModules from '@/shared/AssetModules';
import Chips from '@/components/common/Chips';
import { project_visibility } from '@/types/enums';
import { projectVisibilityOptionsType } from '@/store/types/ICreateProject';
import RadioButton from '@/components/common/RadioButton';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const projectVisibilityOptions: projectVisibilityOptionsType[] = [
  {
    name: 'project_visibility',
    value: project_visibility.PUBLIC,
    label: 'Public',
  },
  {
    name: 'project_visibility',
    value: project_visibility.PRIVATE,
    label: 'Private',
  },
];

const ProjectDetailsForm = ({ flag }) => {
  useDocumentTitle('Create Project: Project Details');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const isAdmin = useIsAdmin();
  const { hostname } = window.location;
  const defaultHashtags = ['#Field-TM', `#${hostname}-{project_id}`];

  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const organisationListData = useAppSelector((state) => state.createproject.organisationList);
  const organisationListLoading = useAppSelector((state) => state.createproject.organisationListLoading);
  const userList = useAppSelector((state) => state.user.userListForSelect)?.map((user) => ({
    id: user.sub,
    label: user.username,
    value: user.sub,
  }));
  const userListLoading = useAppSelector((state) => state.user.userListLoading);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);

  const organisationList = organisationListData.map((item) => ({
    id: item.id,
    label: item.name,
    value: item.id,
    hasODKCredentials: item?.odk_central_url ? true : false,
  }));
  const [hasODKCredentials, setHasODKCredentials] = useState(false);
  const [userSearchText, setUserSearchText] = useState('');
  const [hashtag, setHashtag] = useState('');

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
    dispatch(
      OrganisationService(isAdmin ? `${VITE_API_URL}/organisation` : `${VITE_API_URL}/organisation/my-organisations`),
    );
  };

  useEffect(() => {
    window.addEventListener('focus', onFocus);
    onFocus();
    // Calls onFocus when the window first loads
    return () => {
      window.removeEventListener('focus', onFocus);
    };
  }, []);

  const handleInputChanges = (e) => {
    handleChange(e);
    dispatch(CreateProjectActions.SetIsUnsavedChanges(true));
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
    if (!userSearchText) return;
    if (!values.organisation_id && userSearchText) {
      dispatch(CommonActions.SetSnackBar({ message: 'Please select an organization', variant: 'warning' }));
      return;
    }

    dispatch(
      GetUserListForSelect(`${VITE_API_URL}/users/usernames`, {
        search: userSearchText,
        signin_type: 'osm',
      }),
    );
  }, [userSearchText]);

  useEffect(() => {
    if (isEmpty(organisationList)) return;
    organisationList?.map((organization) => {
      if (values?.organisation_id == organization?.value) {
        setHasODKCredentials(organization.hasODKCredentials);
      }
    });
  }, [organisationList]);

  useEffect(() => {
    if (!authDetails || isEmpty(organisationList)) return;
    if (!isAdmin && authDetails && authDetails?.orgs_managed?.length === 1) {
      handleOrganizationChange(authDetails?.orgs_managed[0]);
    }
  }, [authDetails, organisationListData]);

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
            {/* if user is organization-admin of only one org, then disable the dropdown & preselect the org */}
            <Select2
              options={organisationList || []}
              disabled={!isAdmin && authDetails && authDetails?.orgs_managed?.length === 1}
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
          {/* Custom ODK creds toggle */}
          <div
            className="fmtm-flex fmtm-flex-col fmtm-gap-6"
            onMouseOver={() => {
              dispatch(CreateProjectActions.SetDescriptionToFocus('projectdetails-odk'));
            }}
            onMouseLeave={() => dispatch(CreateProjectActions.SetDescriptionToFocus(null))}
          >
            {hasODKCredentials && (
              <CustomCheckbox
                key="useDefaultODKCredentials"
                label="Use default or requested ODK credentials"
                checked={values.useDefaultODKCredentials}
                onCheckedChange={() => {
                  handleCustomChange('useDefaultODKCredentials', !values.useDefaultODKCredentials);
                }}
                className="fmtm-text-black"
                labelClickable={hasODKCredentials} // Dynamically set labelClickable based on hasODKCredentials
              />
            )}
            {((!values.useDefaultODKCredentials && hasODKCredentials) || !hasODKCredentials) && (
              <ODKCredentialsFields values={values} errors={errors} handleChange={handleChange} />
            )}
          </div>
          {/* Select project admin */}
          <div>
            <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold !fmtm-bg-transparent">Assign Project Admin</p>
            <Select2
              name="project_admins"
              options={userList || []}
              value={values.project_admins}
              onChange={(value: any) => {
                handleCustomChange('project_admins', value);
              }}
              placeholder="Search for Field-TM users"
              className="naxatw-w-1/5 naxatw-min-w-[9rem]"
              multiple
              checkBox
              isLoading={userListLoading}
              handleApiSearch={(value) => {
                if (value) {
                  setUserSearchText(value);
                } else {
                  dispatch(UserActions.SetUserListForSelect([]));
                }
              }}
            />
          </div>
          {/* Hashtags */}
          <div>
            <div className="fmtm-flex fmtm-items-end">
              <InputTextField
                id="hashtags"
                label="Hashtags"
                value={hashtag}
                onChange={(e) => {
                  setHashtag(e.target.value);
                }}
                fieldType="text"
                errorMsg={errors.hashtag}
                classNames="fmtm-flex-1"
              />
              <Button
                disabled={!hashtag.trim()}
                variant="primary-red"
                className="!fmtm-rounded-full fmtm-w-8 fmtm-h-8 fmtm-max-h-8 fmtm-max-w-8 fmtm-mx-2 fmtm-mb-[2px]"
                onClick={() => {
                  if (!hashtag.trim()) return;
                  handleCustomChange('hashtags', [...values.hashtags, hashtag]);
                  setHashtag('');
                }}
              >
                <AssetModules.AddIcon />
              </Button>
            </div>
            <div className="fmtm-flex fmtm-items-center fmtm-flex-wrap fmtm-gap-2 fmtm-my-2">
              {defaultHashtags.map((tag, i) => (
                <div
                  key={i}
                  className="fmtm-body-md fmtm-px-2 fmtm-border-[1px] fmtm-bg-grey-100 fmtm-rounded-[40px] fmtm-flex fmtm-w-fit fmtm-items-center fmtm-gap-1"
                >
                  <p>{tag}</p>
                </div>
              ))}
              <Chips
                data={values.hashtags}
                clearChip={(i) => {
                  handleCustomChange(
                    'hashtags',
                    values.hashtags.filter((_, index) => index !== i),
                  );
                }}
              />
            </div>
            <p className="fmtm-text-sm fmtm-text-gray-500 fmtm-leading-4 fmtm-mt-2">
              *Hashtags related to what is being mapped. By default {defaultHashtags} is included. Hashtags are
              sometimes used for analysis later, but should be human informative and not overused, #group #event
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
          <RadioButton
            value={values?.visibility || ''}
            topic="Project Type"
            options={projectVisibilityOptions}
            direction="row"
            onChangeData={(value) => {
              handleCustomChange('visibility', value);
            }}
            errorMsg={errors.visibility}
            hoveredOption={() => {
              dispatch(CreateProjectActions.SetDescriptionToFocus('projectdetails-visibility'));
            }}
          />
          <CustomCheckbox
            key="use_odk_collect"
            label="Use ODK Collect Mobile App (instead of Web Forms)"
            checked={values.use_odk_collect}
            onCheckedChange={() => {
              handleCustomChange('use_odk_collect', !values.use_odk_collect);
            }}
            className="fmtm-text-black"
          />
          <div className="fmtm-w-fit fmtm-mx-auto fmtm-mt-10">
            <Button variant="primary-red" type="submit">
              NEXT
            </Button>
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
