import TextArea from '../../components/common/TextArea';
import InputTextField from '../../components/common/InputTextField';
import React, { useEffect } from 'react';
import { CreateProjectActions } from '../../store/slices/CreateProjectSlice';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../types/reduxTypes';
import useForm from '../../hooks/useForm';
import CreateProjectValidation from '../../components/createproject/validation/CreateProjectValidation';
import Button from '../../components/common/Button';
import { CommonActions } from '../../store/slices/CommonSlice';
import AssetModules from '../../shared/AssetModules.js';
import { createPopup } from '../../utilfunctions/createPopup';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/common/Select';
import { OrganisationService } from '../../api/CreateProjectService';
import environment from '../../environment';

const ProjectDetailsForm = ({ flag }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const projectDetails: any = useAppSelector((state) => state.createproject.projectDetails);
  const organizationListData: any = useAppSelector((state) => state.createproject.organizationList);

  const organizationList = organizationListData.map((item) => ({ label: item.name, value: item.id }));

  const submission = () => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(values));
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: 2 }));
    navigate('/upload-area');
  };

  const { handleSubmit, handleCustomChange, values, errors }: any = useForm(
    projectDetails,
    submission,
    CreateProjectValidation,
  );

  const onFocus = () => {
    dispatch(OrganisationService(`${environment.baseApiUrl}/organization/`));
  };
  useEffect(() => {
    window.addEventListener('focus', onFocus);
    onFocus();
    // Calls onFocus when the window first loads
    return () => {
      window.removeEventListener('focus', onFocus);
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

  return (
    <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row">
      <div className="fmtm-bg-white xl:fmtm-w-[17%] fmtm-px-5 fmtm-py-6">
        <h6 className="fmtm-text-xl fmtm-font-[600] fmtm-pb-2 lg:fmtm-pb-6">Project Details</h6>
        <p className="fmtm-text-gray-500 lg:fmtm-flex lg:fmtm-flex-col lg:fmtm-gap-3">
          <span>Fill in your project basic information such as name, description, hashtag, etc. </span>
          <span>To complete the first step, you will need the account credentials of ODK central server.</span>{' '}
          <span>Here are the instructions for setting up a Central ODK Server on Digital Ocean.</span>
        </p>
      </div>

      <form
        className="xl:fmtm-w-[83%] lg:fmtm-h-[60vh] xl:fmtm-h-[58vh] fmtm-bg-white fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar"
        onSubmit={handleSubmit}
      >
        <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 md:fmtm-w-[50%]">
            <InputTextField
              id="name"
              label="Project Name"
              value={values?.name}
              onChange={(e) => handleCustomChange('name', e.target.value)}
              fieldType="text"
              required
              errorMsg={errors.name}
            />
            <TextArea
              id="short_description"
              label="Short Description"
              rows={3}
              value={values?.short_description}
              onChange={(e) => handleCustomChange('short_description', e.target.value)}
              required
              errorMsg={errors.short_description}
            />
            <InputTextField
              id="odk_central_url"
              label="ODK Central URL"
              value={values?.odk_central_url}
              onChange={(e) => handleCustomChange('odk_central_url', e.target.value)}
              fieldType="text"
              required
              errorMsg={errors.odk_central_url}
            />
            <InputTextField
              id="odk_central_user"
              label="Central ODK Email/Username"
              value={values?.odk_central_user}
              onChange={(e) => handleCustomChange('odk_central_user', e.target.value)}
              fieldType="text"
              required
              errorMsg={errors.odk_central_user}
            />
            <InputTextField
              id="odk_central_password"
              label="Central ODK Password"
              value={values?.odk_central_password}
              onChange={(e) => handleCustomChange('odk_central_password', e.target.value)}
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
            <div>
              <div className="fmtm-flex fmtm-gap-1">
                <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold ">Organization Name</p>
                <p className="fmtm-text-red-500 fmtm-text-[1.2rem]">*</p>
              </div>
              <div className="fmtm-flex fmtm-items-end ">
                <div className="fmtm-w-[25rem]">
                  <Select
                    value={values?.organisation_id?.toString()}
                    onValueChange={(value) => handleCustomChange('organisation_id', parseInt(value))}
                  >
                    <SelectTrigger className="">
                      <SelectValue placeholder="Select an Organization" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        {organizationList?.map((org) => (
                          <SelectItem key={org.value} value={org?.value?.toString()}>
                            {org.label}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </div>
                <AssetModules.AddIcon
                  className="fmtm-bg-red-600 fmtm-text-white fmtm-rounded-full fmtm-mb-[0.15rem] hover:fmtm-bg-red-700 hover:fmtm-cursor-pointer fmtm-ml-5"
                  onClick={() => createPopup('Create Organization', 'createOrganization?popup=true')}
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
