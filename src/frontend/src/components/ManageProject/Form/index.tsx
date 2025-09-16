import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import UploadArea from '@/components/common/UploadArea';
import Button from '@/components/common/Button';
import CoreModules from '@/shared/CoreModules';
import { PostFormUpdate } from '@/api/CreateProjectService';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useDownloadFormQuery } from '@/api/central';
import { downloadBlobData } from '@/utilfunctions';
import { CommonActions } from '@/store/slices/CommonSlice';

const API_URL = import.meta.env.VITE_API_URL;

type FileType = {
  id: string;
  file: File;
  previewURL: string;
};

const FormUpdate = ({ projectId }) => {
  useDocumentTitle('Manage Project: Form Update');
  const dispatch = useAppDispatch();

  const [uploadForm, setUploadForm] = useState<FileType[] | null>([]);
  const [formError, setFormError] = useState(false);

  const xFormId = CoreModules.useAppSelector((state) => state.createproject.editProjectDetails.odk_form_id);
  const formUpdateLoading = useAppSelector((state) => state.createproject.formUpdateLoading);

  const onSave = () => {
    if (uploadForm?.length === 0) {
      setFormError(true);
      return;
    }
    dispatch(
      PostFormUpdate(`${API_URL}/central/update-form?project_id=${projectId}`, {
        xformId: xFormId,
        upload: uploadForm && uploadForm?.[0]?.file,
      }),
    );
  };

  const {
    data: formBlobData,
    isSuccess: isDownloadFormSuccess,
    error: downloadFormError,
    isLoading: isDownloadFormLoading,
    refetch: downloadForm,
  } = useDownloadFormQuery({
    params: { project_id: +projectId },
    options: { queryKey: ['get-download-form', +projectId], enabled: false },
  });

  useEffect(() => {
    if (isDownloadFormSuccess && formBlobData) {
      downloadBlobData(formBlobData, `project_form_${projectId}`, 'xlsx');
    }
  }, [isDownloadFormSuccess, formBlobData]);

  useEffect(() => {
    const handleBlobErrorResponse = async (blob: Blob | undefined) => {
      if (!blob) return;
      const errorMsg = JSON.parse(await blob?.text())?.detail;
      dispatch(
        CommonActions.SetSnackBar({
          message: errorMsg || 'Failed to download',
        }),
      );
    };

    if (downloadFormError) {
      handleBlobErrorResponse(downloadFormError?.response?.data);
    }
  }, [downloadFormError]);

  return (
    <div className="fmtm-relative fmtm-flex fmtm-flex-col fmtm-w-full fmtm-h-full fmtm-bg-white">
      <div className="fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9 fmtm-flex fmtm-flex-col fmtm-gap-y-5 fmtm-flex-1 fmtm-overflow-y-scroll scrollbar">
        <div>
          <p className="fmtm-text-base">⚠️ IMPORTANT ⚠️</p>
          <p className="fmtm-text-base fmtm-mt-2">
            Please{' '}
            <a
              className={`fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline ${isDownloadFormLoading && 'fmtm-pointer-events-none fmtm-cursor-not-allowed'}`}
              onClick={() => downloadForm()}
              aria-disabled={isDownloadFormLoading}
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
      </div>
      <div className="fmtm-py-2 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-shadow-2xl fmtm-z-50">
        <Button variant="primary-red" onClick={onSave} isLoading={formUpdateLoading}>
          UPDATE
        </Button>
      </div>
    </div>
  );
};

export default FormUpdate;
