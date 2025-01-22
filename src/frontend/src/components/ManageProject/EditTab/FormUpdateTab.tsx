import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import UploadArea from '@/components/common/UploadArea';
import Button from '@/components/common/Button';
import { CustomSelect } from '@/components/common/Select';
import CoreModules from '@/shared/CoreModules';
import { FormCategoryService } from '@/api/CreateProjectService';
import { DownloadProjectForm } from '@/api/Project';
import { PostFormUpdate } from '@/api/CreateProjectService';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const API_URL = import.meta.env.VITE_API_URL;

type FileType = {
  id: string;
  file: File;
  previewURL: string;
};

const FormUpdateTab = ({ projectId }) => {
  useDocumentTitle('Manage Project: Form Update');
  const dispatch = useAppDispatch();

  const [uploadForm, setUploadForm] = useState<FileType[] | null>([]);
  const [formError, setFormError] = useState(false);

  const xFormId = CoreModules.useAppSelector((state) => state.createproject.editProjectDetails.odk_form_id);
  const formCategoryList = useAppSelector((state) => state.createproject.formCategoryList);
  const sortedFormCategoryList = formCategoryList.slice().sort((a, b) => a.title.localeCompare(b.title));
  const selectedCategory = useAppSelector((state) => state.createproject.editProjectDetails.xform_category);
  const formUpdateLoading = useAppSelector((state) => state.createproject.formUpdateLoading);

  useEffect(() => {
    dispatch(FormCategoryService(`${API_URL}/central/list-forms`));
  }, []);

  const onSave = () => {
    if (uploadForm?.length === 0) {
      setFormError(true);
      return;
    }
    dispatch(
      PostFormUpdate(`${API_URL}/projects/update-form?project_id=${projectId}`, {
        xformId: xFormId,
        category: selectedCategory,
        upload: uploadForm && uploadForm?.[0]?.file,
      }),
    );
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-10">
      <div className="">
        <CustomSelect
          title="What are you Surveying"
          placeholder="Survey Type"
          data={sortedFormCategoryList}
          dataKey="id"
          valueKey="title"
          label="title"
          value={selectedCategory}
          className="fmtm-max-w-[13.5rem]"
          disabled
        />
        <p className="fmtm-text-base fmtm-mt-2">
          The survey type will be used to set the OpenStreetMap{' '}
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
        <p className="fmtm-text-base">⚠️ IMPORTANT ⚠️</p>
        <p className="fmtm-text-base fmtm-mt-2">
          Please{' '}
          <a
            className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
            onClick={() =>
              dispatch(DownloadProjectForm(`${API_URL}/projects/download-form/${projectId}`, 'form', projectId))
            }
          >
            download
          </a>{' '}
          {`your form and modify it, before re-uploading below.`}
        </p>
        <p className="fmtm-text-base fmtm-mt-2">Do not upload the original form, as it has since been updated.</p>
      </div>
      <div>
        <UploadArea
          title="Upload Form"
          label="Please upload .xls, .xlsx, .xml file"
          data={uploadForm || []}
          onUploadFile={(updatedFiles) => {
            setUploadForm(updatedFiles as FileType[]);
            formError && setFormError(false);
          }}
          acceptedInput=".xls, .xlsx, .xml"
        />
        {formError && <p className="fmtm-text-primaryRed fmtm-text-sm fmtm-pt-1">Please upload a form</p>}
      </div>
      <div className="fmtm-flex fmtm-justify-center">
        <Button
          isLoading={formUpdateLoading}
          loadingText="UPDATE"
          onClick={onSave}
          btnText="UPDATE"
          btnType="primary"
          className="fmtm-rounded-md"
        />
      </div>
    </div>
  );
};

export default FormUpdateTab;
