import React, { useState } from 'react';
import TextArea from '@/components/common/TextArea';
import InputTextField from '@/components/common/InputTextField';
import Button from '@/components/common/Button';
import EditProjectValidation from '@/components/ManageProject/Details/validation/EditDetailsValidation';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { PatchProjectDetails } from '@/api/CreateProjectService';
import { diffObject } from '@/utilfunctions/compareUtils';
import useForm from '@/hooks/useForm';
import { CommonActions } from '@/store/slices/CommonSlice';
import RichTextEditor from '@/components/common/Editor/Editor';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import Chips from '@/components/common/Chips';
import RadioButton from '@/components/common/RadioButton';
import { projectVisibilityOptionsType } from '@/store/types/ICreateProject';
import { project_status, project_visibility } from '@/types/enums';
import { projectStatusOptionsType } from '@/store/types/IProject';

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

const projectStatusOptions: projectStatusOptionsType[] = [
  {
    name: 'project_status',
    value: project_status.PUBLISHED,
    label: 'Published',
  },
  {
    name: 'project_status',
    value: project_status.COMPLETED,
    label: 'Completed',
  },
];

const EditDetails = ({ projectId }) => {
  useDocumentTitle('Manage Project: Project Description');
  const dispatch = useAppDispatch();

  const [hashtag, setHashtag] = useState('');

  const editProjectDetails = useAppSelector((state) => state.createproject.editProjectDetails);
  const editProjectDetailsLoading = useAppSelector((state) => state.createproject.editProjectDetailsLoading);

  const submission = () => {
    const changedValues = diffObject(editProjectDetails, values);
    dispatch(CreateProjectActions.SetIndividualProjectDetails(values));
    if (Object.keys(changedValues).length > 0) {
      dispatch(PatchProjectDetails(`${VITE_API_URL}/projects/${projectId}`, changedValues));
    } else {
      dispatch(
        CommonActions.SetSnackBar({
          message: 'No changes to Save',
          variant: 'info',
        }),
      );
    }
  };

  const { handleSubmit, handleChange, handleCustomChange, values, errors }: any = useForm(
    editProjectDetails,
    submission,
    EditProjectValidation,
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="fmtm-relative fmtm-w-full fmtm-h-full fmtm-flex fmtm-flex-col fmtm-overflow-hidden fmtm-bg-white"
    >
      <div className="fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9 fmtm-flex-1 fmtm-overflow-y-scroll scrollbar fmtm-flex fmtm-flex-col fmtm-gap-6">
        <RadioButton
          value={values?.status || ''}
          topic="Project Status"
          options={projectStatusOptions}
          direction="column"
          onChangeData={(value) => {
            handleCustomChange('status', value);
          }}
        />
        <InputTextField
          id="name"
          name="name"
          label="Project Name"
          value={values?.name}
          onChange={handleChange}
          fieldType="text"
          classNames="fmtm-w-full"
          errorMsg={errors.name}
          required
        />
        <TextArea
          id="short_description"
          name="short_description"
          label="Short Description"
          rows={2}
          value={values?.short_description}
          onChange={handleChange}
          errorMsg={errors.short_description}
          required
          maxLength={200}
        />
        <TextArea
          id="description"
          name="description"
          label="Description"
          rows={3}
          value={values?.description}
          onChange={handleChange}
          errorMsg={errors.description}
          required
        />
        <div>
          <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold">Instructions</p>
          <RichTextEditor
            editorHtmlContent={values?.per_task_instructions}
            setEditorHtmlContent={(content) => handleCustomChange('per_task_instructions', content)}
            editable={true}
          />
        </div>
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
          <Chips
            className="fmtm-my-2"
            data={values?.hashtags}
            clearChip={(i) => {
              handleCustomChange(
                'hashtags',
                values.hashtags.filter((_, index) => index !== i),
              );
            }}
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
        />
      </div>
      <div className="fmtm-py-2 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-shadow-2xl fmtm-z-50">
        <Button variant="primary-red" isLoading={editProjectDetailsLoading} type="submit">
          SAVE
        </Button>
      </div>
    </form>
  );
};

export default EditDetails;
