import React, { useEffect, useState } from 'react';
import CoreModules from '../../shared/CoreModules.js';
import AssetModules from '../../shared/AssetModules.js';
import EditProjectArea from 'map/EditProjectArea';
import enviroment from '../../environment';
import { EditProjectBoundaryService, GetDividedTaskFromGeojson } from '../../api/CreateProjectService';

const UpdateProjectArea = ({ projectId }) => {
  const dispatch = CoreModules.useAppDispatch();
  const [uploadAOI, setUploadAOI] = useState<any>(null);
  const [geojsonAOI, setGeojsonAOI] = useState<any>(null);
  const [projectBoundaryDetails, setProjectBoundaryDetails] = useState<any>({ dimension: 10 });
  const outline_geojson = CoreModules.useAppSelector((state) => state.createproject.editProjectDetails.outline_geojson);
  const dividedTaskGeojson = CoreModules.useAppSelector((state) => state.createproject.dividedTaskGeojson);
  const dividedTaskGeojsonLoading = CoreModules.useAppSelector((state) => state.createproject.dividedTaskLoading);
  const updateBoundaryLoading = CoreModules.useAppSelector((state) => state.createproject.updateBoundaryLoading);
  const defaultTheme: any = CoreModules.useAppSelector((state) => state.theme.hotTheme);
  const inputFormStyles = () => {
    return {
      style: {
        color: defaultTheme.palette.error.main,
        fontFamily: defaultTheme.typography.fontFamily,
        fontSize: defaultTheme.typography.fontSize,
      },
    };
  };
  useEffect(() => {
    if (!uploadAOI) return;
    const fileReader = new FileReader();
    fileReader.readAsText(uploadAOI, 'UTF-8');
    fileReader.onload = (e: ProgressEvent<FileReader>) => {
      const parsedGeojson = e.target?.result;
      setGeojsonAOI(parsedGeojson);
    };
  }, [uploadAOI]);

  useEffect(() => {
    if (!outline_geojson) return;
    setGeojsonAOI(outline_geojson);
    if (!dividedTaskGeojson) return;
    setGeojsonAOI(dividedTaskGeojson);
  }, [dividedTaskGeojson, outline_geojson]);

  const generateTasksOnMap = () => {
    dispatch(
      GetDividedTaskFromGeojson(`${enviroment.baseApiUrl}/projects/preview_tasks/`, {
        geojson: uploadAOI,
        dimension: projectBoundaryDetails?.dimension,
      }),
    );
  };
  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(
      EditProjectBoundaryService(
        `${enviroment.baseApiUrl}/projects/edit_project_boundary/${projectId}/`,
        uploadAOI,
        projectBoundaryDetails?.dimension,
      ),
    );
  };
  return (
    <form onSubmit={handleSubmit}>
      <CoreModules.Stack flexDirection="row">
        <CoreModules.Stack sx={{ width: '45%' }}>
          <CoreModules.FormLabel>Upload Geojson </CoreModules.FormLabel>
          <CoreModules.Button variant="contained" component="label">
            <CoreModules.Input
              type="file"
              onChange={(e) => {
                setUploadAOI(e.target.files[0]);
              }}
              inputProps={{ accept: '.geojson, .json' }}
            />
            {/* <CoreModules.Typography component="h4">{customFormFile?.name}</CoreModules.Typography> */}
          </CoreModules.Button>
          <CoreModules.FormControl sx={{ mb: 3, width: '100%' }}>
            <CoreModules.Box sx={{ display: 'flex', flexDirection: 'row' }}>
              <CoreModules.FormLabel component="h3">Dimension (in metre)</CoreModules.FormLabel>
            </CoreModules.Box>
            <CoreModules.Stack
              sx={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '20px',
              }}
            >
              <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', width: '50%' }}>
                <CoreModules.TextField
                  id="dimension"
                  label=""
                  type="number"
                  min="9"
                  inputProps={{ sx: { padding: '8.5px 14px' } }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '&.Mui-focused fieldset': {
                        borderColor: 'black',
                      },
                    },
                  }}
                  value={projectBoundaryDetails?.dimension}
                  onChange={(e) => {
                    setProjectBoundaryDetails({ dimension: e.target.value });
                  }}
                  InputProps={{ inputProps: { min: 9 } }}
                  FormHelperTextProps={inputFormStyles()}
                />
              </CoreModules.Stack>
              <CoreModules.LoadingButton
                disabled={projectBoundaryDetails?.dimension < 10}
                onClick={generateTasksOnMap}
                loading={dividedTaskGeojsonLoading}
                loadingPosition="end"
                endIcon={<AssetModules.SettingsSuggestIcon />}
                variant="contained"
                color="error"
              >
                Generate Tasks
              </CoreModules.LoadingButton>
            </CoreModules.Stack>
          </CoreModules.FormControl>
          <CoreModules.Stack sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
            <CoreModules.LoadingButton
              disabled={updateBoundaryLoading}
              type="submit"
              loading={updateBoundaryLoading}
              loadingPosition="end"
              // endIcon={<AssetModules.SettingsSuggestIcon />}
              variant="contained"
              color="error"
              // onClick={onSubmit}
            >
              Submit
            </CoreModules.LoadingButton>
          </CoreModules.Stack>
        </CoreModules.Stack>
        <CoreModules.Stack sx={{ width: '100%' }}>
          <EditProjectArea geojson={geojsonAOI} />
        </CoreModules.Stack>
      </CoreModules.Stack>
    </form>
  );
};

export default UpdateProjectArea;
