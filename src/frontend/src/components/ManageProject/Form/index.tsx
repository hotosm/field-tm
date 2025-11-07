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
import AssetModules from '@/shared/AssetModules';

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
        <div className="fmtm-border fmtm-border-yellow-400 fmtm-rounded-xl fmtm-bg-yellow-50 fmtm-py-3 fmtm-px-5">
          <div className="fmtm-flex fmtm-gap-2 fmtm-items-center fmtm-mb-1">
            <AssetModules.AssignmentIcon className=" fmtm-text-yellow-500" sx={{ fontSize: '20px' }} />
            <h5 className="fmtm-text-[1rem] fmtm-font-semibold">Steps to follow:</h5>
          </div>
          <div>
            <p className="fmtm-body-md">
              Download the{' '}
              <a
                className={`fmtm-text-blue-600 hover:fmtm-text-blue-700 fmtm-cursor-pointer fmtm-underline ${isDownloadFormLoading && 'fmtm-pointer-events-none fmtm-cursor-not-allowed'}`}
                onClick={() => downloadForm()}
                aria-disabled={isDownloadFormLoading}
              >
                latest version
              </a>{' '}
              of your form from this page.
            </p>
            <p className="fmtm-body-md">Edit the form as needed.</p>
            <p className="fmtm-body-md">Re-upload the updated version here.</p>
            <p className="fmtm-body-md">Ensure your changes stay compatible with the project&apos;s current setup.</p>
          </div>
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
