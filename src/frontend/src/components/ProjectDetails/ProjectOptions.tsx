import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import Button from '@/components/common/Button';
import { useAppSelector } from '@/types/reduxTypes';
import { GetProjectQrCode } from '@/api/Files';
import { useDownloadFormQuery } from '@/api/central';
import { useDownloadFeaturesQuery, useDownloadTaskBoundariesQuery } from '@/api/project';
import { downloadBlobData } from '@/utilfunctions';
import { useDispatch } from 'react-redux';
import { CommonActions } from '@/store/slices/CommonSlice';

type downloadTypeType = 'form' | 'geojson' | 'extract' | 'submission' | 'qr';
type downloadButtonType = { downloadType: downloadTypeType; label: string; isLoading: boolean; show: boolean };

const ProjectOptions = () => {
  const params = useParams();
  const dispatch = useDispatch();

  const projectId = params.id!;
  const projectInfo = useAppSelector((state) => state.project.projectInfo);

  const odkToken = useAppSelector((state) => state.project.projectInfo.odk_token);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const { qrcode }: { qrcode: string } = GetProjectQrCode(odkToken, projectInfo.name, authDetails?.username);

  const {
    error: downloadFormError,
    isLoading: isDownloadFormLoading,
    refetch: downloadForm,
  } = useDownloadFormQuery({
    params: { project_id: +projectId },
    options: { queryKey: ['get-download-form', +projectId], enabled: false },
  });

  const {
    error: downloadTaskBoundariesError,
    isLoading: isDownloadTaskBoundariesLoading,
    refetch: downloadTaskBoundaries,
  } = useDownloadTaskBoundariesQuery({
    project_id: +projectId,
    options: { queryKey: ['get-download-task-boundary', +projectId], enabled: false },
  });

  const {
    error: downloadFeaturesError,
    isLoading: isDownloadFeaturesLoading,
    refetch: downloadFeatures,
  } = useDownloadFeaturesQuery({
    params: { project_id: +projectId },
    options: { queryKey: ['get-download-features', +projectId], enabled: false },
  });

  const downloadQr = () => {
    const downloadLink = document.createElement('a');
    downloadLink.href = qrcode;
    downloadLink.download = `Project_${projectId}.png`;
    downloadLink.click();
  };

  const downloadButtonList: downloadButtonType[] = [
    {
      downloadType: 'form',
      label: 'FORM',
      isLoading: isDownloadFormLoading,
      show: true,
    },
    {
      downloadType: 'geojson',
      label: 'TASKS',
      isLoading: isDownloadTaskBoundariesLoading,
      show: true,
    },
    { downloadType: 'extract', label: 'MAP FEATURES', isLoading: isDownloadFeaturesLoading, show: true },
    { downloadType: 'qr', label: 'QR CODE', isLoading: false, show: projectInfo.use_odk_collect || false },
  ];

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

    if (downloadFormError || downloadTaskBoundariesError || downloadFeaturesError) {
      handleBlobErrorResponse(
        downloadFormError?.response?.data ||
          downloadTaskBoundariesError?.response?.data ||
          downloadFeaturesError?.response?.data,
      );
    }
  }, [downloadFormError, downloadTaskBoundariesError, downloadFeaturesError]);

  const handleDownload = async (downloadType: downloadTypeType) => {
    switch (downloadType) {
      case 'form':
        const { data: formBlobData } = await downloadForm();
        if (formBlobData) downloadBlobData(formBlobData, `project_form_${projectId}`, 'xlsx');
        break;
      case 'geojson':
        const { data: taskBoundariesBlobData } = await downloadTaskBoundaries();
        if (taskBoundariesBlobData) downloadBlobData(taskBoundariesBlobData, `task_boundaries_${projectId}`, 'geojson');
        break;
      case 'extract':
        const { data: featuresBlobData } = await downloadFeatures();
        if (featuresBlobData) downloadBlobData(featuresBlobData, `features_${projectId}`, 'geojson');
        break;
      case 'qr':
        downloadQr();
        break;
    }
  };

  return (
    <div className="fmtm-flex fmtm-gap-2 fmtm-flex-col">
      {downloadButtonList.map(
        (btn) =>
          btn.show && (
            <Button
              key={btn.downloadType}
              variant="secondary-grey"
              onClick={() => handleDownload(btn.downloadType)}
              isLoading={btn.isLoading}
            >
              {btn.label}
              <AssetModules.FileDownloadIcon style={{ fontSize: '20px' }} />
            </Button>
          ),
      )}
    </div>
  );
};

export default ProjectOptions;
