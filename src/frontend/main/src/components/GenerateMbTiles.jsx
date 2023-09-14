import React, { useEffect, useState } from 'react';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import environment from '../environment';
import { DownloadTile, GenerateProjectTiles, GetTilesList } from '../api/Project';

const GenerateMbTiles = ({ setToggleGenerateModal, toggleGenerateModal, projectInfo }) => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const encodedId = params.id;
  const decodedId = environment.decode(encodedId);
  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const generateProjectTilesLoading = CoreModules.useAppSelector((state) => state.project.generateProjectTilesLoading);
  const tilesList = CoreModules.useAppSelector((state) => state.project.tilesList);
  const [selectedTileSource, setSelectedTileSource] = useState(null);

  const modalStyle = (theme) => ({
    // width: "30%",
    // height: "24%",
    bgcolor: theme.palette.mode === 'dark' ? '#0A1929' : 'white',
    border: '1px solid ',
    padding: '16px 32px 24px 32px',
  });
  console.log(projectInfo, 'projectInfo');
  const downloadMbTiles = (tileId) => {
    dispatch(DownloadTile(`${environment.baseApiUrl}/projects/download_tiles/?tile_id=${tileId}`, projectInfo));
  };
  const getTilesList = () => {
    dispatch(GetTilesList(`${environment.baseApiUrl}/projects/tiles_list/${decodedId}/`));
  };
  useEffect(() => {
    //Only fetch tiles list when modal is open
    if (toggleGenerateModal) {
      getTilesList();
    }
  }, [toggleGenerateModal]);
  return (
    <CoreModules.CustomizedModal
      isOpen={!!toggleGenerateModal}
      style={modalStyle}
      toggleOpen={() => setToggleGenerateModal(!toggleGenerateModal)}
    >
      <>
        <CoreModules.IconButton
          aria-label="close"
          onClick={() => setToggleGenerateModal(!toggleGenerateModal)}
          sx={{ width: '50px', float: 'right', display: 'block' }}
        >
          <AssetModules.CloseIcon />
        </CoreModules.IconButton>
        <CoreModules.FormControl sx={{ mb: 3, width: '100%' }}>
          <CoreModules.InputLabel
            id="form-category"
            sx={{
              '&.Mui-focused': {
                color: defaultTheme.palette.black,
              },
            }}
          >
            Select Tiles Source
          </CoreModules.InputLabel>
          <CoreModules.Select
            labelId="form_ways-label"
            id="form_ways"
            value={selectedTileSource}
            label="Form Selection"
            sx={{
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                border: '2px solid black',
              },
            }}
            onChange={(e) => {
              setSelectedTileSource(e.target.value);
              // handleCustomChange("form_ways", e.target.value);
            }}
            // onChange={(e) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'form_ways', value: e.target.value }))}
          >
            {environment.selectFormWays?.map((form) => (
              <CoreModules.MenuItem key={form.value} value={form.value}>
                {form.label}
              </CoreModules.MenuItem>
            ))}
          </CoreModules.Select>
          {/* {errors.form_ways && (
              <CoreModules.FormLabel
                component="h3"
                sx={{ color: defaultTheme.palette.error.main }}
              >
                {errors.form_ways}
              </CoreModules.FormLabel>
            )} */}
        </CoreModules.FormControl>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <CoreModules.LoadingButton
            variant="contained"
            loading={generateProjectTilesLoading}
            color="error"
            sx={{
              width: '20%',
              height: '10%',
              p: 1,
              display: 'flex !important',
            }}
            onClick={() => {
              // setToggleGenerateModal(false);
              dispatch(
                GenerateProjectTiles(
                  `${environment.baseApiUrl}/projects/tiles/${decodedId}?source=${selectedTileSource}`,
                  decodedId,
                ),
              );
              // dispatch(CoreModules.TaskActions.SetJosmEditorError(null));
            }}
          >
            Generate
          </CoreModules.LoadingButton>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <CoreModules.LoadingButton
            variant="outlined"
            loading={generateProjectTilesLoading}
            color="error"
            sx={{
              width: '15%',
              height: '5%',
              p: 1,
              display: 'flex !important',
            }}
            onClick={() => {
              getTilesList();
            }}
          >
            Refresh
          </CoreModules.LoadingButton>
        </div>
        <CoreModules.TableContainer component={CoreModules.Paper} sx={{ height: '400px', overflowY: 'scroll' }}>
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
                <CoreModules.TableRow key={list.name} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                  <CoreModules.TableCell component="th" scope="row">
                    {list.id}
                  </CoreModules.TableCell>
                  <CoreModules.TableCell align="right">{list.tile_source}</CoreModules.TableCell>
                  <CoreModules.TableCell
                    align="right"
                    sx={{
                      color: environment.statusColors[list.status],
                    }}
                  >
                    {/* Changed Success Display to Completed */}
                    {list.status === 'SUCCESS' ? 'COMPLETED' : list.status}
                  </CoreModules.TableCell>
                  <CoreModules.TableCell align="right">
                    {list.status === 'SUCCESS' ? (
                      <AssetModules.FileDownloadIcon
                        sx={{ cursor: 'pointer' }}
                        onClick={() => downloadMbTiles(list.id)}
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
      </>
    </CoreModules.CustomizedModal>
  );
};

GenerateMbTiles.propTypes = {};

export default GenerateMbTiles;
