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

export default function ExploreProjectCard({ data, length }) {
    const [shadow, setShadow] = React.useState('0')
    const [shadowBox, setShadowBox] = React.useState(0)
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
            marginTop: '7%',
            fontFamily: 'ArchivoLight',
            fontSize: 16
        },
        progressBar: {
            marginTop: '10%',

        },
        outlinedButton: {
            fontSize: 14,
            width: 100,
            height: 35,
            marginTop: '5%',
            padding: 0,
            position: 'absolute',
            color: `${enviroment.sysBlackColor}`,
            right: 0,
            borderRadius: 0,
            border: 0,
            backgroundColor: '#ffb833',
            fontFamily: 'ArchivoRegular'


        },
        card: {
            backgroundColor: 'white',
            border: "1px solid #ffe4b3",
            marginLeft: '0.2%',
            marginRight: '0.2%',
            padding: 0,
            marginTop: '1%',
            width: `${100 / length}%`,
            cursor: 'pointer',
            opacity: 0.9,
            position: 'relative'
        },
        contributors: {
            display: 'flex',
            flexDirection: 'row',

            text: {
                marginTop: '7%',
                fontFamily: 'ArchivoMedium',
                fontSize: 20
            }
        }
    }
    return (
        <Card onClick={() => {
            console.log('clicked')
        }} style={cardInnerStyles.card} sx={{ boxShadow: shadowBox }} onMouseEnter={onFocusIn} onMouseLeave={onFocusOut}>

            <CardContent>

                <Typography sx={{ fontSize: 14, position: 'absolute', right: 7, top: 5, fontFamily: 'ArchivoLight' }} color="text.secondary" gutterBottom>
                    #{data}
                </Typography>

                <div >
                    <Button size="small" variant="contained" style={cardInnerStyles.outlinedButton} disabled>
                        High
                    </Button>
                    {/* <OutlinedButton  color={'warning'} icon={<AccessAlarmIcon />} text="HIGH" style={cardInnerStyles.outlinedButton} /> */}
                    <CustomizedImage status={'card'} style={{ width: 50, height: 50 }} />
                </div>





                <div style={cardInnerStyles.display}>

                    <CustomizedText font={'BarlowBold'} top={'5%'} size={20} text={'Rosso city Mapping'} weight={'bold'} />

                    <Typography style={cardInnerStyles.regularText} sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                        The project aims to map the marginal lakes
                        and floodplains on both banks
                    </Typography>
                </div>

                <div style={cardInnerStyles.contributors}>
                    <Typography style={{ ...cardInnerStyles.contributors.text, color: 'black', opacity: 0.8 }} sx={{ fontSize: 20 }} color="text.secondary" >
                        12
                    </Typography>
                    <Typography style={{ ...cardInnerStyles.regularText, color: 'black', opacity: 0.8, marginLeft: '1%' }} sx={{ fontSize: 14 }} color="text.secondary" >
                        contributors
                    </Typography>
                </div>

                <div className='row'>
                    <div className='col-md-12'>
                        <div className="progress" style={{ marginTop: '2%', height: 8 }}>
                            <div className="progress-bar " role="progressbar" style={{ width: '50%', backgroundColor: '#007acc' }}></div>
                            <div className="progress-bar " role="progressbar" style={{ width: '30%', backgroundColor: '#2db92d' }} ></div>
                            <div className="progress-bar " role="progressbar" style={{ width: '20%', backgroundColor: '#ff3333' }}></div>
                        </div>
                        {/* <CustomizedProgressBar style={cardInnerStyles.progressBar} /> */}
                    </div>
                </div>


                {/* 

                <div className='row'>
                    <div className='col-md-12'>
                        <Typography style={cardInnerStyles.regularText} sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                            Moderate
                        </Typography>
                    </div>

                </div> */}


            </CardContent>

        </Card>
    );
}