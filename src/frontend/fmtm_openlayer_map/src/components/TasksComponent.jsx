
import React, { useState } from "react";
import BasicCard from "fmtm/BasicCard";
// import Activities from "./Activities";
import environment from "fmtm/environment";
import { ProjectFilesById } from "../api/Files";
import { ShareSocial } from 'react-share-social'
import BasicDialog from "../utilities/BasicDialog";
import CustomSwiper from "../utilities/CustomSwiper";
import { HomeActions } from 'fmtm/HomeSlice';
import CoreModules from 'fmtm/CoreModules';
import AssetModules from 'fmtm/AssetModules';

const TasksComponent = ({ type, state, defaultTheme }) => {

    const [open, setOpen] = useState(false)
    const params = CoreModules.useParams();
    const index = state.findIndex(project => project.id == environment.decode(params.id));
    const [selectedTask, SetSelectedTask] = useState(0)
    const validatedSelectedTask = selectedTask == 0 ? state.length != 0 ? state[index].taskBoundries[0].id : null : selectedTask;
    const dispatch = CoreModules.useDispatch();
    const { loading, qrcode } = ProjectFilesById(
        `${environment.baseApiUrl}/projects/${environment.decode(params.id)}`,
        validatedSelectedTask,
        selectedTask
    )
    const socialStyles = {
        copyContainer: {
            border: `1px solid ${defaultTheme.palette.info['main']}`,
            background: defaultTheme.palette.info['info'],
            color: defaultTheme.palette.info['main']
        },
        title: {
            color: defaultTheme.palette.info['main'],
            fontStyle: 'italic'
        }
    }

    return (
        <CoreModules.Box>


            <CoreModules.Stack>
                {
                    loading != true ?
                        <CustomSwiper
                            screenType={type}
                            listOfData={state.length != 0 ? state[index].taskBoundries : []}
                            switchMode="task"
                            selected={selectedTask == 0 ? state[index].taskBoundries[0].id : selectedTask}
                            onClick={(event) => {
                                SetSelectedTask(event.target.id)
                            }}
                            defaultTheme={defaultTheme}
                            loading={loading}
                        />
                        :
                        <CoreModules.Stack direction={'row'} justifyContent={'center'} spacing={1}>
                            {
                                Array.from(Array(
                                    type == 'sm' ? 4 :
                                        type == 's' ? 2 :
                                            type == 'xs' ? 2 : 6)
                                    .fill({ id: 0 }))
                                    .map((skeleton, index) => {
                                        return (
                                            <CoreModules.SkeletonTheme
                                                key={index}
                                                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                                            >
                                                <CoreModules.Skeleton key={skeleton + index} width={200} height={30} />
                                            </CoreModules.SkeletonTheme>
                                        )
                                    })
                            }
                        </CoreModules.Stack>
                }
            </CoreModules.Stack>
            {/* Description section */}
            {/* 
            <Stack direction={'row'} mt={'1%'}>
                <BasicCard
                    title={{ text: 'Project Description', size: 20, weight: 'bold', font: 'sans-serif' }}
                    subtitle={{}}
                    contentProps={{}}
                    variant={'outlined'}
                    headerStatus={true}
                    content={
                        <div>
                            Lorem ipsum dolor sit amet consectetur adipisicing elit. Maxime mollitia,
                            molestiae quas vel sint commodi repudiandae consequuntur voluptatum laborum
                            numquam blanditiis harum quisquam eius sed odit fugiat iusto fuga praesentium
                            optio, eaque rerum! Provident similique accusantium nemo autem. Veritatis
                            obcaecati tenetur iure eius earum ut molestias architecto voluptate aliquam
                            nihil, eveniet aliquid culpa officia aut! Impedit sit sunt quaerat, odit,
                            tenetur error, harum nesciunt ipsum debitis quas aliquid. Reprehenderit,
                            quia. Quo neque error repudiandae fuga? Ipsa laudantium molestias eos
                            sapiente officiis modi at sunt excepturi expedita sint? Sed quibusdam
                            recusandae alias error harum maxime adipisci amet laborum. Perspiciatis
                            minima nesciunt dolorem! Officiis iure rerum voluptates a cumque velit
                            quibusdam sed amet tempora. Sit laborum ab, eius fugit doloribus tenetur
                            fugiat, temporibus enim commodi iusto libero magni deleniti quod quam
                            consequuntur! Commodi minima excepturi repudiandae velit hic maxime
                            doloremque. Quaerat provident commodi consectetur veniam similique ad
                            earum omnis ipsum saepe, voluptas, hic voluptates pariatur est explicabo
                            fugiat, dolorum eligendi quam cupiditate excepturi mollitia maiores labore
                            suscipit quas? Nulla, placeat. Voluptatem quaerat non architecto ab laudantium
                            modi minima sunt esse temporibus sint culpa, recusandae aliquam numquam
                            totam ratione voluptas quod exercitationem fuga. Possimus quis earum veniam
                            quasi aliquam eligendi, placeat qui corporis!
                        </div>
                    }
                />

            </Stack> */}

            <CoreModules.Stack direction={type == 's' ? 'column' : type == 'xs' ? 'column' : 'row'} spacing={2} mt={'1%'}>

                <BasicCard
                    subtitle={{}}
                    contentProps={{}}
                    variant={'elevation'}
                    headerStatus={true}
                    content={

                        <CoreModules.Stack direction={'column'} justifyContent={'center'}>

                            <CoreModules.Stack direction={'row'} justifyContent={'center'}>
                                <CoreModules.Typography
                                    variant="h2"
                                >
                                    {`Task #${validatedSelectedTask}`}
                                </CoreModules.Typography>
                            </CoreModules.Stack>

                            <CoreModules.Stack direction={'row'} justifyContent={'center'}>
                                {
                                    loading ?
                                        <CoreModules.Stack>
                                            <CoreModules.SkeletonTheme
                                                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                                            >
                                                <CoreModules.Skeleton width={300} count={12} />
                                            </CoreModules.SkeletonTheme>
                                        </CoreModules.Stack>
                                        :
                                        <img src={`data:image/png;base64,${qrcode}`} alt="qrcode" />
                                }
                            </CoreModules.Stack>

                            <CoreModules.Stack mt={'1.5%'} direction={'row'} justifyContent={'center'} spacing={5}>
                                <CoreModules.Stack
                                    width={50}
                                    height={50}
                                    borderRadius={55}
                                    boxShadow={2}
                                    justifyContent={'center'}
                                >
                                    <CoreModules.IconButton onClick={() => {
                                        const linkSource = `data:image/png;base64,${qrcode}`;
                                        const downloadLink = document.createElement("a");
                                        downloadLink.href = linkSource;
                                        downloadLink.download = `Task_${validatedSelectedTask}`;
                                        downloadLink.click();
                                    }} disabled={loading} color="info" aria-label="download qrcode">
                                        <AssetModules.FileDownloadIcon sx={{ fontSize: 30, }} />
                                    </CoreModules.IconButton>
                                </CoreModules.Stack>

                                <CoreModules.Stack
                                    width={50}
                                    height={50}
                                    borderRadius={55}
                                    boxShadow={2}
                                    justifyContent={'center'}
                                >

                                    <CoreModules.IconButton onClick={() => {
                                        setOpen(true)
                                    }} disabled={loading} color="info" aria-label="share qrcode">
                                        <AssetModules.ShareIcon sx={{ fontSize: 30 }} />
                                    </CoreModules.IconButton>

                                    <BasicDialog
                                        title={"Share with"}
                                        actions={<ShareSocial
                                            url={`Task_${validatedSelectedTask}`}
                                            socialTypes={['whatsapp', 'twitter']}
                                            onSocialButtonClicked={data => console.log(data)}
                                            style={socialStyles}
                                        />}
                                        onClose={() => {
                                            setOpen(false)
                                        }}
                                        open={open}
                                    />


                                </CoreModules.Stack>

                            </CoreModules.Stack>
                        </CoreModules.Stack>
                    }
                />

                <BasicCard
                    subtitle={{}}
                    contentProps={{}}
                    variant={'elevation'}
                    headerStatus={true}
                    content={
                        <CoreModules.Stack direction={'column'} spacing={1}>

                            <CoreModules.Stack direction={'row'} justifyContent={'center'}>
                                <CoreModules.Typography
                                    variant="h2"
                                >
                                    {`Task #${validatedSelectedTask}`}
                                </CoreModules.Typography>
                            </CoreModules.Stack>


                            {
                                loading ?

                                    <CoreModules.SkeletonTheme
                                        baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                        highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                                    >
                                        <CoreModules.Skeleton width={'100%'} height={30} />
                                    </CoreModules.SkeletonTheme>
                                    :
                                    <CoreModules.Button
                                        variant="contained"
                                        color="error"
                                        startIcon={<AssetModules.VerifiedIcon />}
                                        disabled={loading}
                                        onClick={() => {
                                            dispatch(HomeActions.SetSnackBar({
                                                open: true,
                                                message: `No action yet`,
                                                variant: 'warning',
                                                duration: 6000
                                            }))
                                        }}
                                    >
                                        Mark as mapped
                                    </CoreModules.Button>
                            }

                            {
                                loading ?

                                    <CoreModules.SkeletonTheme
                                        baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                                        highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
                                    >
                                        <CoreModules.Skeleton width={'100%'} height={30} />
                                    </CoreModules.SkeletonTheme>
                                    :
                                    <CoreModules.Button
                                        variant="contained"
                                        color="error"
                                        startIcon={<AssetModules.LockOpenIcon />}
                                        disabled={loading}
                                        onClick={() => {
                                            dispatch(HomeActions.SetSnackBar({
                                                open: true,
                                                message: `No action yet`,
                                                variant: 'warning',
                                                duration: 6000
                                            }))
                                        }}
                                    >
                                        Unlock Task
                                    </CoreModules.Button>
                            }

                            {/* Comments section  */}
                            {/* <Button
                                variant="contained"
                                color="error"
                                startIcon={<DescriptionIcon />}
                            >
                                Task Details
                            </Button>

                            <BasicCard
                                title={{}}
                                subtitle={{}}
                                contentProps={{}}
                                variant={'outlined'}
                                headerStatus={false}
                                content={<Activities />}
                            />


                            <BasicCard
                                title={{}}
                                subtitle={{}}
                                contentProps={{}}
                                variant={'outlined'}
                                headerStatus={false}
                                content={<Activities />}
                            /> */}

                            {/* <BasicTextField others={{ style: { width: '100%' } }} label={""} defaultValue={""} multiline={true} variant={'outlined'} rows={4} placeholder={"write a comment"} /> */}
                        </CoreModules.Stack>
                    }
                />

            </CoreModules.Stack>
        </CoreModules.Box>
    )

}

export default TasksComponent;