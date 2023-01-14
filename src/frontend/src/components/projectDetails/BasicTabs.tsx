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
    const { windowSize, type } = windowDimention();
    const viewMode = type == 'xl' ? 6 : type == 'lg' ? 5 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1

    const handleChange = (event, newValue) => {
        setValue(newValue);
    };

    return (
        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', backgroundColor: 'whitesmoke' }}>
            <Box sx={{ borderColor: 'divider', flexDirection: 'row', justifyContent: 'center' }}>
                <Tabs TabIndicatorProps={{ sx: { bgcolor: 'whitesmoke' } }} variant='fullWidth' value={value} onChange={handleChange} aria-label="basic tabs example">
                    <Tab style={{ color: enviroment.sysRedColor }} label="Activities" {...a11yProps(0)} />
                    <Tab style={{ color: enviroment.sysRedColor }} label="My Tasks" {...a11yProps(1)} />
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
                Item Two
            </TabPanel>
        </Box>
    );
}

