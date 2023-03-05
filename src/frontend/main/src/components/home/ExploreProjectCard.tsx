import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CustomizedImage from '../../utilities/CustomizedImage';
import CustomizedProgressBar from '../../utilities/CustomizedProgressBar';
import { useNavigate } from "react-router-dom";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { Stack } from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import environment from '../../environment';
import { HomeActions } from '../../store/slices/HomeSlice';
import { HomeProjectCardModel } from '../../models/home/homeModel';

//Explore Project Card Model to be renderd in home view
export default function ExploreProjectCard({ data }) {

    const [shadowBox, setShadowBox] = React.useState(0)
    const dispatch = useDispatch();
    const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
    //use navigate hook for from react router dom for rounting purpose
    const navigate = useNavigate();

    //on mounse enter an Element set shadow to 3
    const onHoverIn = () => {
        setShadowBox(3)
    }
    //on mounse enter an Element set shadow to default
    const onHoverOut = () => {
        setShadowBox(0)
    }

    //Inline styles mainly for overidding css
    const cardInnerStyles: any = {
        outlinedButton: {
            width: 100,
            height: 35,
            marginTop: '5%',
            position: 'absolute',
            fontFamily: defaultTheme.typography.h3.fontFamily,
            backgroundColor: defaultTheme.palette.warning['main'],
            color: defaultTheme.palette.warning['contrastText'],
            right: 0,
            borderRadius: 0,
        },
        card: {
            border: `1px solid ${defaultTheme.palette.warning['main']}`,
            marginLeft: '0.1%',
            marginRight: '0.1%',
            marginTop: '0.7%',
            width: `${100}%`,
            cursor: 'pointer',
            opacity: 0.9,
            position: 'relative',
        },

        location: {
            icon: {
                marginTop: '7%',
                fontSize: 22
            }
        }
    }
    return (
        <Card onClick={() => {
            const project: HomeProjectCardModel = data;
            dispatch(HomeActions.SetSelectedProject(project))
            navigate(`/project_details/${environment.encode(data.id)}`)
        }}
            style={cardInnerStyles.card}
            sx={{ boxShadow: shadowBox }}
            onMouseEnter={onHoverIn}
            onMouseLeave={onHoverOut}
        >

            <CardContent>
                {/*Id Number*/}
                <Typography
                    variant='h4'
                    position={'absolute'}
                    right={7}
                    top={5}
                    gutterBottom>
                    #{data.id}
                </Typography>
                {/* <======End======> */}

                {/*Priority Button and Image*/}
                <div>
                    <Button
                        size="small"
                        variant="contained"
                        style={cardInnerStyles.outlinedButton}
                        color="warning"
                        disabled
                    >
                        {data.priority_str}
                    </Button>
                    <CustomizedImage
                        status={'card'}
                        style={{ width: 50, height: 50 }}
                    />
                </div>
                {/* <======End======> */}

                {/*Project Info and description*/}
                <Stack direction={'column'} height={170} mt={'2%'} justifyContent={'left'}>

                    <Typography
                        ml={'2%'}
                        mt={'5%'}
                        variant='subtitle1'
                        color="info"
                        gutterBottom>
                        {data.title}
                    </Typography>

                    <Stack direction={'row'}>
                        <LocationOnIcon
                            color='error'
                            style={cardInnerStyles.location.icon}
                        />
                        <Typography
                            mt={'7%'}
                            variant='h2'
                            color="info"
                            gutterBottom>
                            {data.location_str}
                        </Typography>
                    </Stack>

                    <Typography
                        mt={'7%'}
                        ml={'2%'}
                        variant="h4"
                        color="info"
                        gutterBottom
                    >
                        {data.description}
                    </Typography>

                </Stack>
                {/* <======End======> */}


                {/* Contributors */}
                <Stack direction={'row'}>
                    <Typography
                        mt={'7%'}
                        ml={'2%'}
                        variant={'h2'}
                        fontSize={defaultTheme.typography.subtitle1.fontSize}
                        fontWeight={'bold'}
                        color="info"
                    >
                        {data.num_contributors}
                    </Typography>

                    <Typography
                        mt={'8%'}
                        ml={'2%'}
                        variant={'h4'}
                        fontSize={defaultTheme.typography.htmlFontSize}
                        color="info"
                    >
                        contributors
                    </Typography>
                </Stack>
                {/* <======End======> */}


                {/* Contribution Progress Bar */}
                <CustomizedProgressBar data={data} height={7} />
                {/* <======End======> */}
            </CardContent>

        </Card>
    );
}