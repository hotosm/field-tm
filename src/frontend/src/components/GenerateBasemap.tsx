import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import AssetModules from '@/shared/AssetModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import environment from '@/environment';
import { DownloadBasemapFile } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { projectInfoType } from '@/models/project/projectModel';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useGenerateProjectBasemapMutation, useGetTilesListQuery } from '@/api/project';
import { basemap_providers, tile_output_formats } from '@/types/enums';
import { Dialog, DialogContent } from '@/components/RadixComponents/Dialog';
import Select2 from '@/components/common/Select2';
import { Input } from '@/components/RadixComponents/Input';
import Button from '@/components/common/Button';
import FieldLabel from '@/components/common/FieldLabel';
import ErrorMessage from '@/components/common/ErrorMessage';
import DataTable from '@/components/common/DataTable';

const statusClasses = {
  SUCCESS: 'fmtm-bg-green-50 fmtm-text-green-700 fmtm-border-green-700',
  PENDING: 'fmtm-bg-yellow-50 fmtm-text-yellow-500 fmtm-border-yellow-500',
  FAILED: 'fmtm-bg-red-50 fmtm-text-red-500 fmtm-border-red-500',
};

const GenerateBasemap = ({ projectInfo }: { projectInfo: Partial<projectInfoType> }) => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const id = params.id as string;

  const [selectedTileSource, setSelectedTileSource] = useState<basemap_providers>();
  const [selectedOutputFormat, setSelectedOutputFormat] = useState<tile_output_formats>();
  const [tmsUrl, setTmsUrl] = useState('');
  const [error, setError] = useState<string[]>([]);

  const toggleGenerateMbTilesModal = useAppSelector((state) => state.project.toggleGenerateMbTilesModal);

  const tileDataColumns = [
    {
      header: 'Source',
      accessorKey: 'tile_source',
      cell: ({ getValue }) => {
        return <p className="fmtm-capitalize">{getValue()}</p>;
      },
    },
    {
      header: 'Format',
      accessorKey: 'format',
      cell: ({ getValue }) => {
        return <p className="fmtm-capitalize">{getValue()}</p>;
      },
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: ({ getValue }) => {
        const status = getValue();
        return (
          <div
            className={`${statusClasses[status]} fmtm-border-[1px] fmtm-rounded-full fmtm-px-4 fmtm-py-1 fmtm-w-fit fmtm-text-xs`}
          >
            {status === 'SUCCESS' ? 'COMPLETED' : status}
          </div>
        );
      },
    },
    {
      header: ' ',
      cell: ({ row }: any) => {
        const { status, format, url } = row?.original;
        return (
          <div className="fmtm-flex fmtm-gap-4 fmtm-float-right">
            {status === 'SUCCESS' && format === 'pmtiles' && (
              <AssetModules.VisibilityOutlinedIcon
                sx={{ cursor: 'pointer', fontSize: '22px' }}
                onClick={() => dispatch(ProjectActions.SetPmtileBasemapUrl(url))}
                className="fmtm-text-red-500 hover:fmtm-text-red-700"
              />
            )}
            {status === 'SUCCESS' && (
              <AssetModules.FileDownloadIcon
                sx={{ cursor: 'pointer', fontSize: '22px' }}
                onClick={() => dispatch(DownloadBasemapFile(url))}
                className="fmtm-text-gray-500 hover:fmtm-text-blue-500"
              />
            )}
            <AssetModules.DeleteIcon
              sx={{ cursor: 'pointer', fontSize: '22px' }}
              onClick={() =>
                dispatch(
                  CommonActions.SetSnackBar({
                    message: 'Not implemented',
                  }),
                )
              }
              className="fmtm-text-red-500 hover:fmtm-text-red-700"
            ></AssetModules.DeleteIcon>
          </div>
        );
      },
    },
  ];

  useEffect(() => {
    if (projectInfo?.custom_tms_url) {
      setSelectedTileSource(basemap_providers.esri);
      setTmsUrl(projectInfo?.custom_tms_url);
    }
  }, [projectInfo]);

  const {
    data: tilesList,
    isLoading: isTilesListLoading,
    refetch: refetchTilesList,
  } = useGetTilesListQuery({
    id: +id,
    options: { queryKey: ['get-tiles-list', +id], enabled: toggleGenerateMbTilesModal },
  });

  const handleTileSourceChange = (value: basemap_providers) => {
    setSelectedTileSource(value);
    if (value !== basemap_providers.custom) setTmsUrl('');
  };

  const { mutate: generateProjectBasemapMutate, isPending: generateProjectBasemapPending } =
    useGenerateProjectBasemapMutation({
      id: +id,
      options: {
        onSuccess: ({ data }) => {
          dispatch(CommonActions.SetSnackBar({ message: data.Message, variant: 'success' }));
          refetchTilesList();
        },
        onError: ({ response }) => {
          dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to generate basemap' }));
        },
      },
    });

  const validateFields = () => {
    const currentError: string[] = [];
    if (!selectedTileSource) currentError.push('selectedTileSource');
    if (!selectedOutputFormat) currentError.push('selectedOutputFormat');
    if (!tmsUrl && selectedTileSource === 'custom') currentError.push('tmsUrl');
    setError(currentError);
    return currentError;
  };

  const generateProjectTiles = () => {
    if (!id) return;
    const currentErrors = validateFields();
    if (currentErrors.length === 0)
      generateProjectBasemapMutate({
        tile_source: selectedTileSource!,
        file_format: selectedOutputFormat!,
        tms_url: tmsUrl,
      });
  };

  return (
    <Dialog
      open={!!toggleGenerateMbTilesModal}
      onOpenChange={() => {
        dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(!toggleGenerateMbTilesModal));
      }}
    >
      <DialogContent className="!fmtm-w-fit !fmtm-max-w-[80vw] fmtm-p-2">
        <div className="fmtm-max-h-[90vh] fmtm-flex fmtm-flex-col fmtm-w-full fmtm-h-full fmtm-gap-4 fmtm-px-3">
          <div className="fmtm-grid fmtm-grid-cols-1 sm:fmtm-grid-cols-3 fmtm-w-full fmtm-gap-x-5 fmtm-gap-y-4 sm:fmtm-gap-y-2 fmtm-items-start">
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Select Tile Source" astric />
              <Select2
                options={environment.baseMapProviders || []}
                value={selectedTileSource}
                onChange={handleTileSourceChange}
                placeholder="Select Tile Source"
                choose="value"
              />
              {error.includes('selectedTileSource') && <ErrorMessage message="Tile Source is Required" />}
            </div>
            {selectedTileSource === 'custom' && (
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
                <FieldLabel label="Enter TMS URL" astric />
                <Input value={tmsUrl} onChange={(e) => setTmsUrl(e.target.value)} placeholder="Enter TMS URL" />
                {error.includes('tmsUrl') && <ErrorMessage message="TMS URL is Required" />}
              </div>
            )}
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
              <FieldLabel label="Select Output Format" astric />
              <Select2
                options={environment.tileOutputFormats || []}
                value={selectedOutputFormat}
                onChange={setSelectedOutputFormat}
                placeholder="Select Output Format"
                choose="value"
              />
              {error.includes('selectedOutputFormat') && <ErrorMessage message="Output Format is Required" />}
            </div>
            <div
              className={`fmtm-flex fmtm-gap-2 fmtm-h-fit fmtm-w-full ${error.length > 0 ? 'fmtm-my-auto' : 'fmtm-mt-auto'}`}
            >
              <Button
                variant="primary-red"
                onClick={generateProjectTiles}
                className="!fmtm-w-1/2"
                isLoading={generateProjectBasemapPending}
                disabled={isTilesListLoading}
              >
                GENERATE
              </Button>
              <Button
                variant="secondary-red"
                onClick={() => refetchTilesList()}
                disabled={isTilesListLoading || generateProjectBasemapPending}
                className="!fmtm-w-1/2"
              >
                REFRESH
              </Button>
            </div>
          </div>

          <DataTable
            data={tilesList || []}
            columns={tileDataColumns}
            isLoading={isTilesListLoading}
            tableWrapperClassName="fmtm-flex-1"
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default GenerateBasemap;
