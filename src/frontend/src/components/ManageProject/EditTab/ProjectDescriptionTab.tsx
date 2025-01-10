import React from 'react';
import TextArea from '../../common/TextArea';
import InputTextField from '../../common/InputTextField';
import Button from '../../common/Button';
import EditProjectValidation from '@/components/ManageProject/EditTab/validation/EditProjectDetailsValidation';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { PatchProjectDetails } from '@/api/CreateProjectService';
import { diffObject } from '@/utilfunctions/compareUtils';
import useForm from '@/hooks/useForm';
import { CommonActions } from '@/store/slices/CommonSlice';
import RichTextEditor from '@/components/common/Editor/Editor';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';

const ProjectDescriptionTab = ({ projectId }) => {
  useDocumentTitle('Manage Project: Project Description');
  const dispatch = useAppDispatch();
  const editProjectDetails = useAppSelector((state) => state.createproject.editProjectDetails);
  const editProjectDetailsLoading = useAppSelector((state) => state.createproject.editProjectDetailsLoading);

  const submission = () => {
    const changedValues = diffObject(editProjectDetails, values);
    dispatch(CreateProjectActions.SetIndividualProjectDetails(values));
    if (Object.keys(changedValues).length > 0) {
      dispatch(PatchProjectDetails(`${import.meta.env.VITE_API_URL}/projects/${projectId}`, changedValues));
    } else {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'No changes to Save',
          variant: 'info',
          duration: 2000,
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
    <form onSubmit={handleSubmit} className="fmtm-w-full fmtm-h-full fmtm-flex fmtm-flex-col fmtm-flex-grow fmtm-gap-5">
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
      <InputTextField
        id="tags"
        name="hashtags"
        label="Hashtags"
        value={values?.hashtags}
        onChange={handleChange}
        fieldType="text"
        classNames="fmtm-w-full"
        errorMsg={errors.hashtags}
      />
      <div className="fmtm-flex fmtm-justify-center fmtm-mt-4">
        <Button
          isLoading={editProjectDetailsLoading}
          loadingText="Saving"
          btnText="SAVE"
          btnType="primary"
          type="submit"
          className="fmtm-rounded-md"
        />
      </div>
    </form>
  );
};

export default ProjectDescriptionTab;
