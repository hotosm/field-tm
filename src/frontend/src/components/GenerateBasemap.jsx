import React, { useEffect, useState } from 'react';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import environment from '../environment';
import { DownloadTile, GenerateProjectTiles, GetTilesList } from '../api/Project';

const GenerateBasemap = ({ setToggleGenerateModal, toggleGenerateModal, projectInfo }) => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const encodedId = params.id;
  const decodedId = environment.decode(encodedId);
  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const generateProjectTilesLoading = CoreModules.useAppSelector((state) => state.project.generateProjectTilesLoading);
  const tilesList = CoreModules.useAppSelector((state) => state.project.tilesList);
  const [selectedTileSource, setSelectedTileSource] = useState(null);
  const [selectedOutputFormat, setSelectedOutputFormat] = useState(null);
  const [tmsUrl, setTmsUrl] = useState('');

  const modalStyle = (theme) => ({
    width: '90vw', // Responsive modal width using vw
    height: '95vh',
    bgcolor: theme.palette.mode === 'dark' ? '#0A1929' : 'white',
    border: '1px solid ',
    padding: '16px 32px 24px 32px',
  });
  const downloadBasemap = (tileId) => {
    dispatch(DownloadTile(`${import.meta.env.VITE_API_URL}/projects/download_tiles/?tile_id=${tileId}`, projectInfo));
  };

  const getTilesList = () => {
    dispatch(GetTilesList(`${import.meta.env.VITE_API_URL}/projects/tiles_list/${decodedId}/`));
  };

  useEffect(() => {
    // Only fetch tiles list when the modal is open
    if (toggleGenerateModal) {
      getTilesList();
    }
  }, [toggleGenerateModal]);

  const handleTileSourceChange = (e) => {
    setSelectedTileSource(e.target.value);
    // If 'tms' is selected, clear the TMS URL
    if (e.target.value !== 'tms') {
      setTmsUrl('');
    }
  };

  const handleTmsUrlChange = (e) => {
    setTmsUrl(e.target.value);
  };

  return (
    <CoreModules.CustomizedModal
      isOpen={!!toggleGenerateModal}
      style={modalStyle}
      toggleOpen={() => setToggleGenerateModal(!toggleGenerateModal)}
    >
      <CoreModules.Grid container spacing={2}>
        {/* Close Button */}
        <CoreModules.Grid item xs={12}>
          <CoreModules.IconButton
            aria-label="close"
            onClick={() => setToggleGenerateModal(!toggleGenerateModal)}
            sx={{ width: '50px', float: 'right', display: 'block' }}
          >
            <AssetModules.CloseIcon />
          </CoreModules.IconButton>
        </CoreModules.Grid>

        {/* Output Format Dropdown */}
        <CoreModules.Grid item xs={12} sm={6}>
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
              label="Form Selection"
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
        </CoreModules.Grid>

        {/* Tile Source Dropdown or TMS URL Input */}
        <CoreModules.Grid item xs={12} sm={6}>
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
              label="Form Selection"
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
            {selectedTileSource === 'tms' && (
              <CoreModules.FormControl>
                <CoreModules.TextField
                  labelId="tms_url-label"
                  id="tms_url"
                  value={tmsUrl}
                  label="Enter Tile Source"
                  fullWidth
                  sx={{
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      border: '2px solid black',
                    },
                  }}
                  onChange={handleTmsUrlChange}
                />
              </CoreModules.FormControl>
            )}
          </CoreModules.FormControl>
        </CoreModules.Grid>

        {/* Generate Button */}
        <CoreModules.Grid item xs={12} sm={6}>
          <CoreModules.LoadingButton
            variant="contained"
            loading={generateProjectTilesLoading}
            color="error"
            fullWidth
            onClick={() => {
              // Check if 'tms' is selected and tmsUrl is not empty
              if (selectedTileSource === 'tms' && !tmsUrl) {
                // Handle error, TMS URL is required
                console.log('TMS URL is required');
                return;
              }

              dispatch(
                GenerateProjectTiles(
                  `${
                    import.meta.env.VITE_API_URL
                  }/projects/tiles/${decodedId}?source=${selectedTileSource}&format=${selectedOutputFormat}&tms=${tmsUrl}`,
                  decodedId,
                ),
              );
            }}
          >
            Generate
          </CoreModules.LoadingButton>
        </CoreModules.Grid>

        {/* Refresh Button */}
        <CoreModules.Grid item xs={12} sm={6}>
          <CoreModules.LoadingButton
            variant="outlined"
            loading={generateProjectTilesLoading}
            color="error"
            fullWidth
            onClick={() => {
              getTilesList();
            }}
          >
            Refresh
          </CoreModules.LoadingButton>
        </CoreModules.Grid>

        {/* Table Content */}
        <CoreModules.Grid item xs={12}>
          <CoreModules.TableContainer component={CoreModules.Paper} sx={{ maxHeight: '50vh', overflowY: 'auto' }}>
            <CoreModules.Table sx={{ minWidth: 650 }} aria-label="simple table">
              <CoreModules.TableHead>
                <CoreModules.TableRow>
                  <CoreModules.TableCell>Id</CoreModules.TableCell>
                  <CoreModules.TableCell align="right">Source</CoreModules.TableCell>
                  <CoreModules.TableCell align="right">Status</CoreModules.TableCell>
                  <CoreModules.TableCell align="right"></CoreModules.TableCell>
                </CoreModules.TableRow>
              </CoreModules.TableHead>
              <CoreModules.TableBody>
                {tilesList.map((list) => (
                  <CoreModules.TableRow key={list.name}>
                    <CoreModules.TableCell component="th" scope="row">
                      {list.id}
                    </CoreModules.TableCell>
                    <CoreModules.TableCell align="right">{list.tile_source}</CoreModules.TableCell>
                    <CoreModules.TableCell align="right" sx={{ color: environment.statusColors[list.status] }}>
                      {list.status === 'SUCCESS' ? 'COMPLETED' : list.status}
                    </CoreModules.TableCell>
                    <CoreModules.TableCell align="right">
                      {list.status === 'SUCCESS' ? (
                        <AssetModules.FileDownloadIcon
                          sx={{ cursor: 'pointer' }}
                          onClick={() => downloadBasemap(list.id)}
                        ></AssetModules.FileDownloadIcon>
                      ) : (
                        <></>
                      )}
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

GenerateBasemap.propTypes = {};

export default GenerateBasemap;
