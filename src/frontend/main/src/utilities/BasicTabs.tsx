import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import windowDimention from '../hooks/WindowDimension';
import { useSelector } from 'react-redux';


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
                    {children}
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

export default function BasicTabs({ listOfData }) {
    const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
    const [value, setValue] = React.useState(0);
    const { type } = windowDimention();
    const variant: any = type == 's' ? 'fullWidth' : type == 'xs' ? 'fullWidth' : 'standard'

    const handleChange = (event, newValue) => {
        setValue(newValue);
    };

    return (
        <Box sx={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center'
        }}>
            <Box sx={{ borderColor: 'divider' }}>
                <Tabs
                    centered
                    textColor='inherit'
                    TabIndicatorProps={{
                        style: { backgroundColor: `${defaultTheme.palette.error['main']}`, }
                    }}
                    variant={variant}
                    value={value}
                    onChange={handleChange}
                    aria-label="basic tabs example"
                >
                    {
                        listOfData.map((item, index) => {
                            return (
                                <Tab
                                    key={index}
                             
                                    sx={{
                                        fontFamily: defaultTheme.typography.h1.fontFamily,
                                        fontSize: defaultTheme.typography.fontSize,
                                        mt: 0.8, mb: 1,
                                        mr: 1,
                                        '&:hover':{
                                            backgroundColor:defaultTheme.palette.mapFeatureColors['bad_rgb']
                                        } 
                                    }}
                                    label={item.label
                                    } {...a11yProps(0)}
                                />
                            )
                        })
                    }
                </Tabs>
            </Box>
            {
                listOfData.map((item, index) => {
                    return (
                        <TabPanel value={value} key={index} index={index}>
                            {
                                item.element
                            }
                        </TabPanel>
                    )
                })
            }
        </Box>
    );
}

