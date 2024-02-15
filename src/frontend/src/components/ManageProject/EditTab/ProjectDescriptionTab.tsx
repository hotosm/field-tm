import React from 'react';
import TextArea from '../../common/TextArea';
import InputTextField from '../../common/InputTextField';
import Button from '../../common/Button';
import EditProjectValidation from '@/components/ManageProject/EditTab/validation/EditProjectDetailsValidation';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { PatchProjectDetails } from '@/api/CreateProjectService';
import { diffObject } from '@/utilfunctions/compareUtils';
import useForm from '@/hooks/useForm';
import CoreModules from '@/shared/CoreModules';
import { CommonActions } from '@/store/slices/CommonSlice';

const ProjectDescriptionTab = ({ projectId }) => {
  const dispatch = CoreModules.useAppDispatch();
  const editProjectDetails: any = CoreModules.useAppSelector((state) => state.createproject.editProjectDetails);
  const editProjectDetailsLoading: boolean = CoreModules.useAppSelector(
    (state) => state.createproject.editProjectDetailsLoading,
  );

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
  const { handleSubmit, handleChange, values, errors }: any = useForm(
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
      />
      <TextArea
        id="description"
        name="description"
        label="Description"
        rows={2}
        value={values?.description}
        onChange={handleChange}
        errorMsg={errors.description}
        required
      />
      <TextArea
        id="instruction"
        name="instruction"
        label="Instruction"
        rows={2}
        value={values?.instruction}
        onChange={handleChange}
        errorMsg={errors.instruction}
      />
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
