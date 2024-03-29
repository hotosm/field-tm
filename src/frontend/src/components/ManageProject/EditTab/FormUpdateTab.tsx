import React, { useState, useEffect } from 'react';
import { useAppSelector } from '@/types/reduxTypes';
import UploadArea from '../../common/UploadArea';
import Button from '../../common/Button';
import { CustomSelect } from '@/components/common/Select';
import CoreModules from '@/shared/CoreModules';
import { FormCategoryService, ValidateCustomForm } from '@/api/CreateProjectService';
import { PostFormUpdate } from '@/api/CreateProjectService';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { CommonActions } from '@/store/slices/CommonSlice';
import { Loader2 } from 'lucide-react';

type FileType = {
  id: string;
  name: string;
  url?: File;
  isDeleted: boolean;
};

const FormUpdateTab = ({ projectId }) => {
  const dispatch = CoreModules.useAppDispatch();

  const [uploadForm, setUploadForm] = useState<FileType[] | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [error, setError] = useState({ formError: '', categoryError: '' });

  const formCategoryList = useAppSelector((state) => state.createproject.formCategoryList);
  const sortedFormCategoryList = formCategoryList.slice().sort((a, b) => a.title.localeCompare(b.title));
  const customFileValidity = useAppSelector((state) => state.createproject.customFileValidity);
  const validateCustomFormLoading = useAppSelector((state) => state.createproject.validateCustomFormLoading);

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

  const validateForm = () => {
    setError({ formError: '', categoryError: '' });
    let isValid = true;
    if (!uploadForm || (uploadForm && uploadForm?.length === 0)) {
      setError((prev) => ({ ...prev, formError: 'Form is required.' }));
      isValid = false;
    }
    if (!selectedCategory) {
      setError((prev) => ({ ...prev, categoryError: 'Category is required.' }));
      isValid = false;
    }
    if (!customFileValidity && uploadForm && uploadForm.length > 0) {
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: 'Your file is invalid',
          variant: 'error',
          duration: 2000,
        }),
      );
      isValid = false;
    }
    return isValid;
  };

  const onSave = () => {
    if (validateForm()) {
      dispatch(
        PostFormUpdate(`${import.meta.env.VITE_API_URL}/projects/update-form?project_id=${projectId}`, {
          category: selectedCategory,
          upload: uploadForm && uploadForm?.[0]?.url,
        }),
      );
    }
  };

  useEffect(() => {
    if (uploadForm && uploadForm?.length > 0 && !customFileValidity) {
      dispatch(ValidateCustomForm(`${import.meta.env.VITE_API_URL}/projects/validate-form`, uploadForm?.[0]?.url));
    }
  }, [uploadForm]);

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-10">
      <div className="">
        <CustomSelect
          title="Select category"
          placeholder="Select category"
          data={sortedFormCategoryList}
          dataKey="id"
          valueKey="title"
          label="title"
          value={selectedCategory}
          onValueChange={(value) => {
            setSelectedCategory(value);
          }}
          className="fmtm-max-w-[13.5rem]"
        />
        {error.categoryError && <p className="fmtm-text-primaryRed fmtm-text-base">{error.categoryError}</p>}
        <p className="fmtm-text-base fmtm-mt-2">
          The category will be used to set the OpenStreetMap{' '}
          <a
            href="https://wiki.openstreetmap.org/wiki/Tags"
            target="_"
            className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
          >
            tags
          </a>{' '}
          {`if uploading the final submissions to OSM.`}
        </p>
      </div>
      <div>
        <UploadArea
          title="Upload Form"
          label="Please upload .xls, .xlsx, .xml file"
          multiple={false}
          data={uploadForm || []}
          filterKey="url"
          onUploadFile={(updatedFiles) => {
            dispatch(CreateProjectActions.SetCustomFileValidity(false));
            setUploadForm(updatedFiles);
          }}
          acceptedInput=".xls, .xlsx, .xml"
        />
        {validateCustomFormLoading && (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mt-2">
            <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-primaryRed" />
            <p className="fmtm-text-base">Validating form...</p>
          </div>
        )}
        {error.formError && <p className="fmtm-text-primaryRed fmtm-text-base">{error.formError}</p>}
      </div>
      <div className="fmtm-flex fmtm-justify-center">
        <Button onClick={onSave} btnText="UPDATE" btnType="primary" className="fmtm-rounded-md" />
      </div>
    </div>
  );
};

export default FormUpdateTab;
