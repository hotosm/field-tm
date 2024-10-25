import React, { useState, useEffect } from 'react';
import { useAppSelector } from '@/types/reduxTypes';
import UploadArea from '../../common/UploadArea';
import Button from '../../common/Button';
import { CustomSelect } from '@/components/common/Select';
import CoreModules from '@/shared/CoreModules';
import { FormCategoryService } from '@/api/CreateProjectService';
import { DownloadProjectForm } from '@/api/Project';
import { PostFormUpdate } from '@/api/CreateProjectService';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

type FileType = {
  id: string;
  name: string;
  url?: File;
  isDeleted: boolean;
};

const FormUpdateTab = ({ projectId }) => {
  useDocumentTitle('Manage Project: Form Update');
  const dispatch = CoreModules.useAppDispatch();

  const [uploadForm, setUploadForm] = useState<FileType[] | null>(null);
  const [error, setError] = useState({ formError: '', categoryError: '' });

  const xFormId = CoreModules.useAppSelector((state) => state.project.projectInfo.odk_form_id);
  const formCategoryList = useAppSelector((state) => state.createproject.formCategoryList);
  const sortedFormCategoryList = formCategoryList.slice().sort((a, b) => a.title.localeCompare(b.title));
  const selectedCategory = useAppSelector((state) => state.createproject.editProjectDetails.xform_category);
  const formUpdateLoading = useAppSelector((state) => state.createproject.formUpdateLoading);

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

  const onSave = () => {
    dispatch(
      PostFormUpdate(`${import.meta.env.VITE_API_URL}/projects/update-form?project_id=${projectId}`, {
        xformId: xFormId,
        category: selectedCategory,
        upload: uploadForm && uploadForm?.[0]?.url,
      }),
    );
  };

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
          className="fmtm-max-w-[13.5rem]"
          disabled
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
        <p className="fmtm-text-base">⚠️ IMPORTANT ⚠️</p>
        <p className="fmtm-text-base fmtm-mt-2">
          Please{' '}
          <a
            className="fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline"
            onClick={() =>
              dispatch(
                DownloadProjectForm(
                  `${import.meta.env.VITE_API_URL}/projects/download-form/${projectId}/`,
                  'form',
                  projectId,
                ),
              )
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
          multiple={false}
          data={uploadForm || []}
          filterKey="url"
          onUploadFile={(updatedFiles: FileType[]) => {
            setUploadForm(updatedFiles);
          }}
          acceptedInput=".xls, .xlsx, .xml"
        />
        {error.formError && <p className="fmtm-text-primaryRed fmtm-text-base">{error.formError}</p>}
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
