import { Box, Button } from "@mui/material";
import React from "react";
import QRCode from "react-qr-code";
import { Stack, TextField } from '@mui/material';
import VerifiedIcon from '@mui/icons-material/Verified';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import DescriptionIcon from '@mui/icons-material/Description';
import CustomSwiper from '../../utilities/CustomSwiper';
import BasicCard from "../../utilities/BasicCard";
import Activities from "./Activities";

const TasksComponent = ({ type }) => {


    return (
        <Box>

            <Stack>
                <CustomSwiper
                    screenType={type}
                    listOfData={[{ count: 1 }, { count: 2 }, { count: 3 }, { count: 4 }, { count: 5 }, { count: 6 }]}
                    switchMode="task"
                />

            </Stack>

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

            </Stack>

            <Stack direction={type == 's' ? 'column' : type == 'xs' ? 'column' : 'row'} spacing={2} mt={'1%'}>

                <BasicCard
                    title={{ text: `Task #${10} QR Code`, size: 20, weight: 'bold', font: 'sans-serif' }}
                    subtitle={{}}
                    contentProps={{}}
                    variant={'elevation'}
                    headerStatus={true}
                    content={
                        <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
                            <QRCode
                                style={{ height: "auto", marginTop: '2%', backgroundColor: 'red' }}
                                value={"Project "}
                                viewBox={`0 0 256 256`}
                            />
                        </div>
                    }
                />

                <BasicCard
                    title={{ text: `Task #${10} Actions`, size: 20, weight: 'bold', font: 'sans-serif' }}
                    subtitle={{}}
                    contentProps={{}}
                    variant={'elevation'}
                    headerStatus={true}
                    content={
                        <Stack direction={'column'} spacing={1}>
                            <Button
                                variant="contained"
                                color="error"
                                startIcon={<VerifiedIcon />}
                            >
                                Mark as mapped
                            </Button>
                            <Button
                                variant="contained"
                                color="error"
                                startIcon={<LockOpenIcon />}
                            >
                                Unlock Task
                            </Button>
                            <Button
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
                            />

                            {/* <BasicTextField others={{ style: { width: '100%' } }} label={""} defaultValue={""} multiline={true} variant={'outlined'} rows={4} placeholder={"write a comment"} /> */}
                        </Stack>
                    }
                />

            </Stack>
        </Box>
    )

}

export default TasksComponent;