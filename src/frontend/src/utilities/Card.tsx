import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Skeleton from 'react-loading-skeleton'
import 'react-loading-skeleton/dist/skeleton.css'
import CustomizedProgressBar from './ProgressBar';
import OutlinedButton from './OutlinedButton';
import CustomizedImage from '../components/CustomizedImage';
import CustomizedText from '../components/CustomizedText';
import AccessAlarmIcon from '@mui/icons-material/AccessAlarm';
import enviroment from '../enviroment';

export default function ExploreProjectCard({ maxWidth }) {
    const [shadow, setShadow] = React.useState('0')
    const [shadowBox,setShadowBox] = React.useState(0)
    const onFocusIn = () => {
        // setShadow('2px 2px 1px 1px #ffd9cc')
        setShadowBox(3)
    }
    const onFocusOut = () => {
        // setShadow('0 0 0 0 #ffffff')
        setShadowBox(0)

    }
    const cardInnerStyles: any = {
        display: {
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'left',
            marginTop: '2%'
        },
        regularText: {
            marginTop: '7%'
        },
        progressBar: {
            marginTop: '10%',

        },
        outlinedButton: {
            fontSize: 14,
            width: 100,
            height: 35,
            marginTop: '5%',

        },
        card: {
            backgroundColor: 'whitesmoke',
            border:"1px solid lightgray",
            marginLeft: '1%',
            marginTop: '1%',
            cursor: 'pointer'
        }
    }
    return (
        <Card onClick={()=>{
            console.log('clicked')
        }} style={cardInnerStyles.card} sx={{ boxShadow: shadowBox}} onMouseEnter={onFocusIn} onMouseLeave={onFocusOut}>

            <CardContent>
                <div >
                    <div style={{ float: 'right' }}>
                        <OutlinedButton color={'warning'} icon={<AccessAlarmIcon />} text="HIGH" style={cardInnerStyles.outlinedButton} />
                    </div>
                    <CustomizedImage />

                </div>


                <div className='row'>
                    <div className='col-md-12 mt-4'>
                        <Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                            #6566654
                        </Typography>
                    </div>
                </div>


                <div style={cardInnerStyles.display}>

                    <CustomizedText top={'5%'} size={22} text={'Rosso city Mapping'} weight={'bold'} font={'verdana'} />
                    <CustomizedText top={'5%'} size={18} text={'Project 2021'} weight={'bold'} font={'verdana'} />

                    <Typography style={cardInnerStyles.regularText} sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                        The project aims to map the marginal lakes
                        and floodplains on both banks
                    </Typography>
                </div>


                <div className='row'>
                    <div className='col-md-12'>
                        <CustomizedProgressBar style={cardInnerStyles.progressBar} />
                    </div>
                </div>


                <Typography style={cardInnerStyles.regularText} sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                    403 contributors
                </Typography>


                <div className='row'>
                    <div className='col-md-12'>
                        <Typography style={cardInnerStyles.regularText} sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                            Moderate
                        </Typography>
                    </div>

                </div>


            </CardContent>

        </Card>
    );
}