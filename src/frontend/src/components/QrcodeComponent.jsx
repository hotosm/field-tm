import React, { useState } from 'react';
import BasicCard from '../utilities/BasicCard';
// import Activities from "./Activities";
import environment from '../environment';
import { ProjectFilesById } from '../api/Files';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
import { HomeActions } from '../store/slices/HomeSlice';

const TasksComponent = ({ type, task, defaultTheme }) => {
  const dispatch = CoreModules.useAppDispatch();
  const [open, setOpen] = useState(false);
  const params = CoreModules.useParams();
  const projectData = CoreModules.useAppSelector((state) => state.project.projectTaskBoundries);
  const currentProjectId = environment.decode(params.id);
  const projectIndex = projectData.findIndex((project) => project.id == currentProjectId);
  const token = CoreModules.useAppSelector((state) => state.login.loginToken);
  const currentStatus = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((indTask, i) => {
      return indTask.id == task;
    })?.[0],
  };
  const checkIfTaskAssignedOrNot =
    currentStatus?.locked_by_username === token?.username || currentStatus?.locked_by_username === null;

  const { loading, qrcode } = ProjectFilesById(
    `${import.meta.env.VITE_API_URL}/tasks/task-list?project_id=${environment.decode(params.id)}`,
    task,
  );

  const socialStyles = {
    copyContainer: {
      border: `1px solid ${defaultTheme.palette.info['main']}`,
      background: defaultTheme.palette.info['info'],
      color: defaultTheme.palette.info['main'],
    },
    title: {
      color: defaultTheme.palette.info['main'],
      fontStyle: 'italic',
    },
  };

  return (
    <CoreModules.Stack>
      {checkIfTaskAssignedOrNot && (
        <CoreModules.Stack direction={type == 's' ? 'column' : type == 'xs' ? 'column' : 'row'} spacing={2} mt={'1%'}>
          <BasicCard
            subtitle={{}}
            contentProps={{}}
            variant={'elevation'}
            headerStatus={true}
            content={
              <CoreModules.Stack direction={'column'} justifyContent={'center'}>
                <CoreModules.Stack direction={'row'} justifyContent={'center'}>
                  <CoreModules.Typography variant="h2">{`Qrcode`}</CoreModules.Typography>
                </CoreModules.Stack>

                <CoreModules.Stack direction={'row'} justifyContent={'center'}>
                  {qrcode == '' ? (
                    <CoreModules.Stack>
                      <CoreModules.SkeletonTheme
                        baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                        highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                      >
                        <CoreModules.Skeleton width={170} count={7} />
                      </CoreModules.SkeletonTheme>
                    </CoreModules.Stack>
                  ) : (
                    <img id="qrcodeImg" src={`data:image/png;base64,${qrcode}`} alt="qrcode" />
                  )}
                </CoreModules.Stack>

                <CoreModules.Stack mt={'1.5%'} direction={'row'} justifyContent={'center'} spacing={5}>
                  <CoreModules.Stack width={40} height={40} borderRadius={55} boxShadow={2} justifyContent={'center'}>
                    <CoreModules.IconButton
                      onClick={() => {
                        const linkSource = `data:image/png;base64,${qrcode}`;
                        const downloadLink = document.createElement('a');
                        downloadLink.href = linkSource;
                        downloadLink.download = `Task_${task}`;
                        downloadLink.click();
                      }}
                      disabled={qrcode == '' ? true : false}
                      color="info"
                      aria-label="download qrcode"
                    >
                      <AssetModules.FileDownloadIcon sx={{ fontSize: defaultTheme.typography.fontSize }} />
                    </CoreModules.IconButton>
                  </CoreModules.Stack>
                  <CoreModules.Button
                    variant="contained"
                    color="error"
                    onClick={() => {
                      document.location.href =
                        'intent://getodk.org/#Intent;scheme=app;package=org.odk.collect.android;end';
                    }}
                  >
                    Go To ODK
                  </CoreModules.Button>
                  <CoreModules.Stack width={40} height={40} borderRadius={55} boxShadow={2} justifyContent={'center'}>
                    <CoreModules.IconButton
                      onClick={() => {
                        dispatch(
                          HomeActions.SetSnackBar({
                            open: true,
                            message: `not implemented`,
                            variant: 'warning',
                            duration: 3000,
                          }),
                        );
                        // setOpen(true);
                      }}
                      disabled={qrcode == '' ? true : false}
                      color="info"
                      aria-label="share qrcode"
                    >
                      <AssetModules.ShareIcon sx={{ fontSize: defaultTheme.typography.fontSize }} />
                    </CoreModules.IconButton>

                    {/* <BasicDialog
                    title={"Share with"}
                    actions={
                      <ShareSocial
                        url={`Task_${task}`}
                        socialTypes={["whatsapp", "twitter"]}
                        onSocialButtonClicked={(data) => console.log(data)}
                        style={socialStyles}
                      />
                    }
                    onClose={() => {
                      setOpen(false);
                    }}
                    open={open}
                  /> */}
                  </CoreModules.Stack>
                </CoreModules.Stack>
              </CoreModules.Stack>
            }
          />
        </CoreModules.Stack>
      )}
    </CoreModules.Stack>
  );
};

export default TasksComponent;
