import React, { useEffect, useRef, useState } from 'react';
import Button from '@/components/common/Button';
import InputTextField from '@/components/common/InputTextField';
import TextArea from '@/components/common/TextArea';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import useForm from '@/hooks/useForm';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import OrganizationDetailsValidation from '@/components/CreateEditOrganization/validation/OrganizationDetailsValidation';
import RadioButton from '@/components/common/RadioButton';
import { useDispatch } from 'react-redux';
import {
  GetIndividualOrganizationService,
  PatchOrganizationDataService,
  PostOrganisationDataService,
} from '@/api/OrganisationService';
import { diffObject } from '@/utilfunctions/compareUtils';
import InstructionsSidebar from '@/components/CreateEditOrganization/InstructionsSidebar';
import { CustomCheckbox } from '@/components/common/Checkbox';
import { organizationTypeOptionsType } from '@/models/organisation/organisationModel';
import { useAppSelector } from '@/types/reduxTypes';

const organizationTypeOptions: organizationTypeOptionsType[] = [
  { name: 'osm_community', value: 'OSM_COMMUNITY', label: 'OSM Community' },
  { name: 'company', value: 'COMPANY', label: 'Company' },
  { name: 'non_profit', value: 'NON_PROFIT', label: 'Non-profit' },
  { name: 'university', value: 'UNIVERSITY', label: 'University' },
  { name: 'other', value: 'OTHER', label: 'Other' },
];

const CreateEditOrganizationForm = ({ organizationId }: { organizationId: string }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const inputFileRef = useRef<any>(null);
  const organisationFormData = useAppSelector((state) => state.organisation.organisationFormData);
  const postOrganisationDataLoading = useAppSelector((state) => state.organisation.postOrganisationDataLoading);
  const postOrganisationData = useAppSelector((state) => state.organisation.postOrganisationData);
  const [previewSource, setPreviewSource] = useState<any>('');

  const submission = () => {
    if (!organizationId) {
      const { fillODKCredentials, ...filteredValues } = values;
      dispatch(PostOrganisationDataService(`${import.meta.env.VITE_API_URL}/organisation`, filteredValues));
    } else {
      const { fillODKCredentials, ...filteredValues } = values;
      const changedValues = diffObject(organisationFormData, filteredValues);
      if (Object.keys(changedValues).length > 0) {
        dispatch(
          PatchOrganizationDataService(`${import.meta.env.VITE_API_URL}/organisation/${organizationId}`, changedValues),
        );
      }
    }
  };

  const { handleSubmit, handleChange, handleCustomChange, values, errors }: any = useForm(
    organisationFormData,
    submission,
    OrganizationDetailsValidation,
  );

  const previewFile = (file: File) => {
    const reader = new FileReader();
    reader.readAsDataURL(file); //reads file as data url (base64 encoding)
    reader.onload = () => {
      if (reader) {
        setPreviewSource(reader?.result);
      }
    };
  };

  // redirect to manage-org page after post success
  useEffect(() => {
    if (postOrganisationData) {
      dispatch(OrganisationAction.postOrganisationData(null));
      dispatch(OrganisationAction.SetOrganisationFormData({}));
      dispatch(
        OrganisationAction.SetConsentDetailsFormData({
          give_consent: '',
          review_documentation: [],
          log_into: [],
          participated_in: [],
        }),
      );
      dispatch(OrganisationAction.SetConsentApproval(false));
      if (searchParams.get('popup') === 'true') {
        window.close();
      } else {
        navigate('/organisation');
      }
    }
  }, [postOrganisationData]);

  useEffect(() => {
    if (organizationId) {
      dispatch(GetIndividualOrganizationService(`${import.meta.env.VITE_API_URL}/organisation/${organizationId}`));
    }
  }, [organizationId]);

  useEffect(() => {
    if (!values?.fillODKCredentials) {
      handleCustomChange('odk_central_url', null);
      handleCustomChange('odk_central_user', null);
      handleCustomChange('odk_central_password', null);
    }
  }, [values?.fillODKCredentials]);

  useEffect(() => {
    handleCustomChange('fillODKCredentials', false);
  }, []);

  useEffect(() => {
    if (organizationId) {
      document.title = 'Edit Organization - Field Mapping Tasking Manager';
    } else {
      document.title = 'Add Organization - Field Mapping Tasking Manager';
    }
  }, []);

  return (
    <div
      className={`fmtm-flex ${
        !organizationId ? 'fmtm-flex-col lg:fmtm-flex-row' : 'fmtm-justify-center'
      } fmtm-gap-5 lg:fmtm-gap-10`}
    >
      {!organizationId && <InstructionsSidebar />}
      <div className="fmtm-bg-white fmtm-w-full lg:fmtm-w-[70%] xl:fmtm-w-[55rem] fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9">
        <h5 className="fmtm-text-[#484848] fmtm-text-2xl fmtm-font-[600] fmtm-pb-3 lg:fmtm-pb-7 fmtm-font-archivo fmtm-tracking-wide">
          Organizational Details
        </h5>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
          <InputTextField
            id="name"
            name="name"
            label="Community or Organization Name"
            subLabel="Please name the local community or organization you are asking to create"
            value={values?.name}
            onChange={handleChange}
            fieldType="text"
            required
            errorMsg={errors.name}
          />
          {!organizationId && (
            <InputTextField
              id="url"
              name="url"
              label="Website URL"
              value={values?.url}
              onChange={handleChange}
              fieldType="text"
              required
              errorMsg={errors.url}
            />
          )}
          <TextArea
            id="description"
            name="description"
            label="Description"
            rows={3}
            value={values?.description}
            onChange={handleChange}
            required
            errorMsg={errors.description}
          />
          <CustomCheckbox
            key="fillODKCredentials"
            label="Fill ODK credentials now"
            checked={values.fillODKCredentials}
            onCheckedChange={() => {
              handleCustomChange('fillODKCredentials', !values.fillODKCredentials);
            }}
            className="fmtm-text-black"
          />
          {values?.fillODKCredentials && (
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
          {!organizationId && (
            <RadioButton
              topic="What type of community or organization are you applying for? "
              options={organizationTypeOptions}
              direction="column"
              value={values.community_type}
              onChangeData={(value) => {
                handleCustomChange('community_type', value);
              }}
              className="fmtm-text-base fmtm-text-[#7A7676] fmtm-mt-1"
              errorMsg={errors.community_type}
              required
            />
          )}
          <div className="flex items-center">
            <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold">Upload Logo</p>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-5">
              <input
                ref={inputFileRef}
                type="file"
                className="fmtm-max-w-[250px]"
                onChange={(e) => {
                  handleCustomChange('logo', e.target?.files?.[0]);
                  if (e.target?.files?.[0]) {
                    previewFile(e.target?.files?.[0]);
                  }
                }}
                accept="image/png, image/gif, image/jpeg"
              />
              {(previewSource || values.logo) && (
                <div className="fmtm-relative fmtm-w-fit">
                  <div className="fmtm-absolute -fmtm-top-3 -fmtm-right-3" title="Remove Logo">
                    <AssetModules.DeleteIcon
                      style={{ fontSize: '28px' }}
                      className="fmtm-text-primaryRed hover:fmtm-text-red-700 fmtm-cursor-pointer"
                      onClick={() => {
                        inputFileRef.current.value = '';
                        handleCustomChange('logo', '');
                        setPreviewSource('');
                      }}
                    />
                  </div>
                  <img
                    src={previewSource ? previewSource : values.logo ? values.logo : ''}
                    alt=""
                    className="fmtm-h-[100px] fmtm-rounded-sm fmtm-border-[1px]"
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-mt-8 lg:fmtm-mt-16">
          {!organizationId && (
            <Button
              btnText="Back"
              btnType="other"
              className="fmtm-font-bold"
              onClick={() => dispatch(OrganisationAction.SetConsentApproval(false))}
            />
          )}
          <Button
            isLoading={postOrganisationDataLoading}
            loadingText={!organizationId ? 'Submitting' : 'Updating'}
            btnText={!organizationId ? 'Submit' : 'Update'}
            btnType="primary"
            className="fmtm-font-bold"
            onClick={handleSubmit}
          />
        </div>
      </div>
    </div>
  );
};

export default CreateEditOrganizationForm;
