import * as React from 'react';
import CustomizedImage from '../../utilities/CustomizedImage';
import CustomizedProgressBar from '../../utilities/CustomizedProgressBar';
import environment from '../../environment';
import { HomeActions } from '../../store/slices/HomeSlice';
import { HomeProjectCardModel } from '../../models/home/homeModel';
import CoreModules from '../../shared/CoreModules';
import AssetModules from '../../shared/AssetModules';

//Explore Project Card Model to be renderd in home view
export default function ExploreProjectCard({ data }) {
    const [shadowBox, setShadowBox] = React.useState(0)
    const dispatch = CoreModules.useDispatch();
    const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)
    //use navigate hook for from react router dom for rounting purpose
    const navigate = CoreModules.useNavigate();

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
        <CoreModules.Card onClick={() => {
            const project: HomeProjectCardModel = data;
            dispatch(HomeActions.SetSelectedProject(project))
            navigate(`/project_details/${environment.encode(data.id)}`)
        }}
            style={cardInnerStyles.card}
            sx={{ boxShadow: shadowBox }}
            onMouseEnter={onHoverIn}
            onMouseLeave={onHoverOut}
        >

            <CoreModules.CardContent>
                {/*Id Number*/}
                <CoreModules.Typography
                    variant='h4'
                    position={'absolute'}
                    right={7}
                    top={5}
                    gutterBottom>
                    #{data.id}
                </CoreModules.Typography>
                {/* <======End======> */}

                {/*Priority Button and Image*/}
                <div>
                    <CoreModules.Button
                        size="small"
                        variant="contained"
                        style={cardInnerStyles.outlinedButton}
                        color="warning"
                        disabled
                    >
                        {data.priority_str}
                    </CoreModules.Button>
                    <CustomizedImage
                        status={'card'}
                        style={{ width: 50, height: 50 }}
                    />
                </div>
                {/* <======End======> */}

                {/*Project Info and description*/}
                <CoreModules.Stack direction={'column'} minHeight={190} mt={'2%'} justifyContent={'left'}>

                    <CoreModules.Typography
                        ml={'2%'}
                        mt={'5%'}
                        variant='subtitle1'
                        color="info"
                        gutterBottom>
                        {data.title}
                    </CoreModules.Typography>

                    <CoreModules.Stack direction={'row'}>
                        <AssetModules.LocationOn
                            color='error'
                            style={cardInnerStyles.location.icon}
                        />
                        <CoreModules.Typography
                            mt={'7%'}
                            variant='h2'
                            color="info"
                            gutterBottom>
                            {data.location_str}
                        </CoreModules.Typography>
                    </CoreModules.Stack>

                    <CoreModules.Typography
                        mt={'7%'}
                        ml={'2%'}
                        variant="h4"
                        color="info"
                        gutterBottom
                    >
                        {data.description}
                    </CoreModules.Typography>

                </CoreModules.Stack>
                {/* <======End======> */}


                {/* Contributors */}
                <CoreModules.Stack direction={'row'}>
                    <CoreModules.Typography
                        mt={'7%'}
                        ml={'2%'}
                        variant={'h2'}
                        fontSize={defaultTheme.typography.subtitle1.fontSize}
                        fontWeight={'bold'}
                        color="info"
                    >
                        {data.num_contributors}
                    </CoreModules.Typography>

                    <CoreModules.Typography
                        mt={'8%'}
                        ml={'2%'}
                        variant={'h4'}
                        fontSize={defaultTheme.typography.htmlFontSize}
                        color="info"
                    >
                        contributors
                    </CoreModules.Typography>
                </CoreModules.Stack>
                {/* <======End======> */}


                {/* Contribution Progress Bar */}
                <CustomizedProgressBar data={data} height={7} />
                {/* <======End======> */}
            </CoreModules.CardContent>

        </CoreModules.Card>
    );
}