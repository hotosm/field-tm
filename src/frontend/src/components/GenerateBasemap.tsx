import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { CommonActions } from '@/store/slices/CommonSlice';
import environment from '@/environment';
import { DownloadBasemapFile } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { projectInfoType } from '@/models/project/projectModel';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useGenerateProjectBasemapMutation, useGetTilesListQuery } from '@/api/project';
import { basemap_providers, tile_output_formats } from '@/types/enums';

const GenerateBasemap = ({ projectInfo }: { projectInfo: Partial<projectInfoType> }) => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const id = params.id as string;

  const [selectedTileSource, setSelectedTileSource] = useState<basemap_providers>();
  const [selectedOutputFormat, setSelectedOutputFormat] = useState<tile_output_formats>();
  const [tmsUrl, setTmsUrl] = useState('');
  const [error, setError] = useState<string[]>([]);

  const toggleGenerateMbTilesModal = useAppSelector((state) => state.project.toggleGenerateMbTilesModal);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  const modalStyle = (theme: Record<string, any>) => ({
    width: '90vw',
    bgcolor: theme.palette.mode === 'dark' ? '#0A1929' : 'white',
    border: '1px solid ',
    padding: '16px 32px 24px 32px',
    maxWidth: '1000px',
  });

  useEffect(() => {
    if (projectInfo?.custom_tms_url) {
      setSelectedTileSource('custom');
      setTmsUrl(projectInfo?.custom_tms_url);
    }
  }, [projectInfo]);

  const {
    data: tilesList,
    isPending: isTilesListPending,
    refetch: refetchTilesList,
  } = useGetTilesListQuery({
    id: +id,
    options: { queryKey: ['get-tiles-list', +id], enabled: toggleGenerateMbTilesModal },
  });

  const handleTileSourceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedTileSource(e.target.value);
    if (e.target.value !== 'custom') setTmsUrl('');
  };

  const { mutate: generateProjectBasemapMutate, isPending: generateProjectBasemapPending } =
    useGenerateProjectBasemapMutation({
      id: +id,
      payload: {
        tile_source: selectedTileSource,
        file_format: selectedOutputFormat,
        tms_url: tmsUrl,
      },
      options: {
        onSuccess: () => refetchTilesList(),
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
    if (currentErrors.length === 0) generateProjectBasemapMutate();
  };

  return (
    <CoreModules.CustomizedModal
      isOpen={!!toggleGenerateMbTilesModal}
      style={modalStyle}
      toggleOpen={() => {
        dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(!toggleGenerateMbTilesModal));
      }}
    >
      <CoreModules.Grid container spacing={2}>
        {/* Close Button */}
        <CoreModules.Grid item xs={12}>
          <CoreModules.IconButton
            aria-label="close"
            onClick={() => {
              dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(!toggleGenerateMbTilesModal));
            }}
            sx={{ width: '50px', float: 'right', display: 'block' }}
          >
            <AssetModules.CloseIcon />
          </CoreModules.IconButton>
        </CoreModules.Grid>

        <CoreModules.Grid container spacing={2} className="fmtm-px-4 fmtm-mb-4">
          {/* Tile Source Dropdown or TMS URL Input */}
          <CoreModules.Grid item xs={12} sm={6} md={4}>
            <CoreModules.FormControl fullWidth>
              <CoreModules.InputLabel
                id="tile-source"
                sx={{
                  '&.Mui-focused': {
                    color: defaultTheme.palette.black,
                  },
                }}
              >
                Select Tile Source
              </CoreModules.InputLabel>
              <CoreModules.Select
                labelId="tile-source"
                id="tile_source"
                value={selectedTileSource}
                label="Select Tile Source"
                fullWidth
                sx={{
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    border: '2px solid black',
                  },
                }}
                onChange={handleTileSourceChange}
              >
                {environment.baseMapProviders?.map((form) => (
                  <CoreModules.MenuItem key={form.value} value={form.value}>
                    {form.label}
                  </CoreModules.MenuItem>
                ))}
              </CoreModules.Select>
            </CoreModules.FormControl>
            {error.includes('selectedTileSource') && (
              <p className="fmtm-text-sm fmtm-text-red-500">Tile Source is Required.</p>
            )}
          </CoreModules.Grid>
          {selectedTileSource === 'custom' && (
            <CoreModules.Grid item xs={12} sm={6} md={4}>
              <CoreModules.FormControl fullWidth>
                <CoreModules.TextField
                  // labelId="tms_url-label"
                  id="tms_url"
                  variant="outlined"
                  value={tmsUrl}
                  label="Enter TMS URL"
                  fullWidth
                  color="black"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '&.Mui-focused fieldset': {
                        borderColor: 'black',
                      },
                    },
                    '&.Mui-focused .MuiFormLabel-root-MuiInputLabel-root': {
                      color: 'black',
                    },
                  }}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTmsUrl(e.target.value)}
                />
              </CoreModules.FormControl>
              {error.includes('tmsUrl') && <p className="fmtm-text-sm fmtm-text-red-500">TMS URL is Required.</p>}
            </CoreModules.Grid>
          )}
          {/* Output Format Dropdown */}
          <CoreModules.Grid item xs={12} sm={6} md={4}>
            <CoreModules.FormControl fullWidth>
              <CoreModules.InputLabel
                id="output-format"
                sx={{
                  '&.Mui-focused': {
                    color: defaultTheme.palette.black,
                  },
                }}
              >
                Select Output Format
              </CoreModules.InputLabel>
              <CoreModules.Select
                labelId="output-format"
                id="output_format"
                value={selectedOutputFormat}
                label="Select Output Format"
                fullWidth
                sx={{
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    border: '2px solid black',
                  },
                }}
                onChange={(e) => {
                  setSelectedOutputFormat(e.target.value);
                }}
              >
                {environment.tileOutputFormats?.map((form) => (
                  <CoreModules.MenuItem key={form.value} value={form.value}>
                    {form.label}
                  </CoreModules.MenuItem>
                ))}
              </CoreModules.Select>
            </CoreModules.FormControl>
            {error.includes('selectedOutputFormat') && (
              <p className="fmtm-text-sm fmtm-text-red-500">Output Format is Required.</p>
            )}
          </CoreModules.Grid>
          <CoreModules.Grid
            item
            xs={12}
            sm={selectedTileSource === 'custom' ? 6 : 12}
            md={selectedTileSource === 'custom' ? 12 : 4}
          >
            <div className="fmtm-w-full fmtm-flex fmtm-items-center fmtm-justify-center sm:fmtm-justify-end fmtm-mr-4 fmtm-gap-4 fmtm-h-full">
              {/* Generate Button */}
              <div>
                <CoreModules.Button
                  variant="contained"
                  loading={generateProjectBasemapPending}
                  color="error"
                  onClick={generateProjectTiles}
                >
                  Generate
                </CoreModules.Button>
              </div>

              {/* Refresh Button */}
              <div>
                <CoreModules.Button
                  variant="outlined"
                  disabled={generateProjectBasemapPending}
                  color="error"
                  onClick={refetchTilesList}
                >
                  Refresh
                </CoreModules.Button>
              </div>
            </div>
          </CoreModules.Grid>
        </CoreModules.Grid>

        {/* Table Content */}
        <CoreModules.Grid item xs={12}>
          <CoreModules.TableContainer
            component={CoreModules.Paper}
            className="scrollbar fmtm-overflow-y-auto fmtm-max-h-[38vh] lg:fmtm-max-h-[45vh] sm:fmtm-mb-5"
          >
            <CoreModules.Table className="fmtm-min-w-[300px] md:fmtm-min-w-[650px]" aria-label="simple table">
              <CoreModules.TableHead>
                <CoreModules.TableRow>
                  {/* <CoreModules.TableCell>Id</CoreModules.TableCell> */}
                  <CoreModules.TableCell align="center">Source</CoreModules.TableCell>
                  <CoreModules.TableCell align="center">Format</CoreModules.TableCell>
                  <CoreModules.TableCell align="center">Status</CoreModules.TableCell>
                  <CoreModules.TableCell align="center"></CoreModules.TableCell>
                </CoreModules.TableRow>
              </CoreModules.TableHead>

              <CoreModules.TableBody>
                {tilesList?.map((list) => (
                  <CoreModules.TableRow key={list.id}>
                    <CoreModules.TableCell align="center">
                      <div className="fmtm-text-primaryRed fmtm-border-primaryRed fmtm-border-[1px] fmtm-rounded-full fmtm-px-4 fmtm-py-1 fmtm-w-fit fmtm-mx-auto">
                        {list.tile_source}
                      </div>
                    </CoreModules.TableCell>
                    <CoreModules.TableCell align="center">
                      <div className="fmtm-text-primaryRed fmtm-border-primaryRed fmtm-border-[1px] fmtm-rounded-full fmtm-px-4 fmtm-py-1 fmtm-w-fit fmtm-mx-auto">
                        {list.format}
                      </div>
                    </CoreModules.TableCell>
                    <CoreModules.TableCell align="center" sx={{ color: environment.statusColors[list.status] }}>
                      {/* {list.status === 'SUCCESS' ? 'COMPLETED' : list.status} */}
                      {list.status === 'SUCCESS' ? (
                        <div className="fmtm-bg-green-50 fmtm-text-green-700 fmtm-border-green-700 fmtm-border-[1px] fmtm-rounded-full fmtm-px-4 fmtm-py-1 fmtm-w-fit fmtm-mx-auto">
                          COMPLETED
                        </div>
                      ) : (
                        <div
                          className={`${
                            list.status === 'PENDING'
                              ? 'fmtm-bg-yellow-50 fmtm-text-yellow-500 fmtm-border-yellow-500'
                              : 'fmtm-bg-red-50 fmtm-text-red-500 fmtm-border-red-500'
                          }  fmtm-border-[1px] fmtm-rounded-full fmtm-px-4 fmtm-py-1 fmtm-w-fit fmtm-mx-auto`}
                        >
                          {list.status}
                        </div>
                      )}
                    </CoreModules.TableCell>
                    <CoreModules.TableCell align="center">
                      <div className="fmtm-flex fmtm-gap-4 fmtm-float-right">
                        {list.status === 'SUCCESS' && list.format === 'pmtiles' && (
                          <AssetModules.VisibilityOutlinedIcon
                            sx={{ cursor: 'pointer', fontSize: '22px' }}
                            onClick={() => dispatch(ProjectActions.SetPmtileBasemapUrl(list.url))}
                            className="fmtm-text-red-500 hover:fmtm-text-red-700"
                          />
                        )}
                        {list.status === 'SUCCESS' && (
                          <AssetModules.FileDownloadIcon
                            sx={{ cursor: 'pointer', fontSize: '22px' }}
                            onClick={() => dispatch(DownloadBasemapFile(list.url))}
                            className="fmtm-text-gray-500 hover:fmtm-text-blue-500"
                          />
                        )}
                        <AssetModules.DeleteIcon
                          sx={{ cursor: 'pointer', fontSize: '22px' }}
                          onClick={() => {
                            dispatch(
                              CommonActions.SetSnackBar({
                                message: 'Not implemented',
                              }),
                            );
                          }}
                          className="fmtm-text-red-500 hover:fmtm-text-red-700"
                        ></AssetModules.DeleteIcon>
                      </div>
                    </CoreModules.TableCell>
                  </CoreModules.TableRow>
                ))}
              </CoreModules.TableBody>
            </CoreModules.Table>
          </CoreModules.TableContainer>
        </CoreModules.Grid>
      </CoreModules.Grid>
    </CoreModules.CustomizedModal>
  );
};

export default GenerateBasemap;
