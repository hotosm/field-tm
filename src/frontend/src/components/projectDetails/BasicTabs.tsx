import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import CustomPwComponents from '../../utilities/CustomPwComponents';
import windowDimention from '../../customHooks/WindowDimension';
import Activities from './Activities';
import BasicCard from '../../utilities/BasicCard';
import enviroment from '../../enviroment';
import QRCode from "react-qr-code";
import { Stack, TextField } from '@mui/material';
import CustomizedButton from '../../utilities/CustomizedButton';
import VerifiedIcon from '@mui/icons-material/Verified';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import DescriptionIcon from '@mui/icons-material/Description';
import BasicTextField from '../../utilities/BasicTextField';
function TabPanel(props) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ p: 3 }}>
                    <Typography>{children}</Typography>
                </Box>
            )}
        </div>
    );
}

TabPanel.propTypes = {
    children: PropTypes.node,
    index: PropTypes.number.isRequired,
    value: PropTypes.number.isRequired,
};

function a11yProps(index) {
    return {
        id: `simple-tab-${index}`,
        'aria-controls': `simple-tabpanel-${index}`,
    };
}

export default function BasicTabs() {
    const [value, setValue] = React.useState(0);
    const [shadow, setShadow] = React.useState({
        activity: 0,
        tasks: 1
    })
    const { windowSize, type } = windowDimention();
    const viewMode = type == 'xl' ? 6 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1

    const TabsStyles = {
        activityTab: {
            backgroundColor: value == 0 ? 'whitesmoke' : 'white',
            color: value == 0 ? enviroment.sysRedColor : enviroment.sysBlackColor,
        },
        tasksTab: {
            backgroundColor: value == 1 ? 'whitesmoke' : 'white',
            color: value == 1 ? enviroment.sysRedColor : enviroment.sysBlackColor
        }
    }
    const hover = (event: Event) => {

    }
    const handleChange = (event, newValue) => {

        if (newValue == 0) {
            setShadow({
                activity: 0,
                tasks: 1
            })
        } else {
            setShadow({
                activity: 1,
                tasks: 0
            })
        }
        setValue(newValue);
    };

    return (
        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', backgroundColor: 'whitesmoke' }}>
            <Box sx={{ borderColor: 'divider', flexDirection: 'row', justifyContent: 'center' }}>
                <Tabs TabIndicatorProps={{ sx: { bgcolor: 'whitesmoke' } }} variant='fullWidth' value={value} onChange={handleChange} aria-label="basic tabs example">
                    <Tab sx={{ mt: 0.8, mb: 1, mr: 1, boxShadow: shadow.activity }} style={TabsStyles.activityTab} label="Activities" {...a11yProps(0)} />
                    <Tab sx={{ mt: 0.8, mb: 1, ml: 1, boxShadow: shadow.tasks }} style={TabsStyles.tasksTab} label="My Tasks" {...a11yProps(1)} />
                </Tabs>
            </Box>
            <TabPanel value={value} index={0}>
                <CustomPwComponents
                    mainComponentStyles={{ width: '100%', }}
                    spacing={1}
                    componentData={new Array(10).fill(0)}
                    element={
                        <BasicCard
                            width={`${100 / viewMode}%`}
                            title={{}}
                            subtitle={{}}
                            contentProps={{}}
                            variant={'elevation'}
                            headerStatus={false}
                            content={<Activities />}
                        />
                    }
                    viewMode={viewMode}
                />
            </TabPanel>
            <TabPanel value={value} index={1}>
                <Stack>
                    <CustomPwComponents
                        mainComponentStyles={{ width: '100%', }}
                        spacing={1}
                        componentData={new Array(10).fill(0)}
                        element={
                            <BasicCard
                                width={`${100 / viewMode}%`}
                                title={{}}
                                subtitle={{}}
                                contentProps={{}}
                                variant={'elevation'}
                                headerStatus={false}
                                content={<Activities />}
                            />
                        }
                        viewMode={viewMode}
                    />
                </Stack>
                <Stack direction={'row'} mt={'1%'}>
                    <BasicCard
                        width={`${100}%`}
                        title={{ text: 'Project Description', size: 20, weight: 'bold', font: 'sans-serif' }}
                        subtitle={{}}
                        contentProps={{}}
                        variant={'outlined'}
                        headerStatus={true}
                        content={<div>
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
                        </div>}
                    />

                </Stack>

                <Stack direction={type == 's' ? 'column' : type == 'xs' ? 'column' : 'row'} spacing={2} mt={'1%'}>
                    <BasicCard
                        width={`${100}%`}
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
                        width={`${100}%`}
                        title={{ text: `Task #${10} Actions`, size: 20, weight: 'bold', font: 'sans-serif' }}
                        subtitle={{}}
                        contentProps={{}}
                        variant={'elevation'}
                        headerStatus={true}
                        content={
                            <Stack direction={'column'} spacing={1}>
                                <CustomizedButton variant={'contained'} color={'error'} text={'Mark as mapped'} icon={<VerifiedIcon />} style={{}} />
                                <CustomizedButton variant={'contained'} color={'error'} text={'Unlock Task'} icon={<LockOpenIcon />} style={{}} />
                                <CustomizedButton variant={'contained'} color={'error'} text={'Task DetailS'} icon={<DescriptionIcon />} style={{}} />

                                <BasicCard
                                    width={`${100}%`}
                                    title={{}}
                                    subtitle={{}}
                                    contentProps={{}}
                                    variant={'outlined'}
                                    headerStatus={false}
                                    content={<Activities />}
                                />


                                <BasicCard
                                    width={`${100}%`}
                                    title={{}}
                                    subtitle={{}}
                                    contentProps={{}}
                                    variant={'outlined'}
                                    headerStatus={false}
                                    content={<Activities />}
                                />

                                <BasicTextField others={{ style: { width: '100%' } }} label={""} defaultValue={""} multiline={true} variant={'outlined'} rows={4} placeholder={"write a comment"} />
                            </Stack>
                        }
                    />

                </Stack>
            </TabPanel>
        </Box>
    );
}

