import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CustomizedImage from '../../utilities/CustomizedImage';
import CustomizedText from '../../utilities/CustomizedText';
import enviroment from '../../enviroment';
import CustomizedProgressBar from '../../utilities/CustomizedProgressBar';
import { useNavigate } from "react-router-dom";
import LocationOnIcon from '@mui/icons-material/LocationOn';

export default function ExploreProjectCard({ data, length }) {
    const [shadowBox, setShadowBox] = React.useState(0)
    const navigate = useNavigate();

    const onFocusIn = () => {
        setShadowBox(3)
    }

    const onFocusOut = () => {
        setShadowBox(0)
    }
    const cardInnerStyles: any = {
        display: {
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'left',
            height: 170,
            marginTop: '2%',

        },
        regularText: {
            marginTop: '7%',
            fontFamily: 'ArchivoLight',
            marginLeft: '2%',
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
            marginLeft: '0.1%',
            marginRight: '0.1%',
            marginTop: '1%',
            width: `${100 / length}%`,
            cursor: 'pointer',
            opacity: 0.9,
            position: 'relative',


        },
        contributors: {
            display: 'flex',
            flexDirection: 'row',
            text: {
                marginTop: '7%',
                fontFamily: 'ArchivoMedium',
                fontSize: 20,
                marginLeft: '2%'
            }
        },
        location: {
            display: 'flex',
            flexDirection: 'row',
            icon: {
                marginTop: '7%',
                fontSize: 22
            }
        }
    }
    return (
        <Card onClick={() => {
            navigate('/project_details')
        }} style={cardInnerStyles.card} sx={{ boxShadow: shadowBox }} onMouseEnter={onFocusIn} onMouseLeave={onFocusOut}>

            <CardContent>
                <Typography sx={{ fontSize: 14, position: 'absolute', right: 7, top: 5, fontFamily: 'ArchivoLight' }} color="text.secondary" gutterBottom>
                    #{data.id}
                </Typography>

                <div>
                    <Button size="small" variant="contained" style={cardInnerStyles.outlinedButton} disabled>
                        {data.priority_str}
                    </Button>
                    <CustomizedImage status={'card'} style={{ width: 50, height: 50 }} />
                </div>



                <div style={cardInnerStyles.display}>

                    <div style={{ marginLeft: '2%', marginTop: '5%' }}>
                        <CustomizedText font={'BarlowBold'} top={'0%'} size={20} text={data.title} weight={'bold'} />
                    </div>

                    <div style={cardInnerStyles.location}>
                        <LocationOnIcon color='error' style={cardInnerStyles.location.icon} />
                        <CustomizedText font={enviroment.mediumText} top={'7%'} size={16} text={data.location_str} weight={'regular'} />
                    </div>
                    <Typography style={cardInnerStyles.regularText} sx={{ fontSize: 14, height: 'inherit' }} color="text.secondary" gutterBottom>
                        {data.description}
                    </Typography>
                </div>

                <div style={cardInnerStyles.contributors}>
                    <Typography style={{ ...cardInnerStyles.contributors.text, color: 'black', opacity: 0.8 }} sx={{ fontSize: 20 }} color="text.secondary" >
                        {data.num_contributors}
                    </Typography>
                    <Typography style={{ ...cardInnerStyles.regularText, marginTop: '8%', color: 'black', opacity: 0.8, marginLeft: '1%' }} sx={{ fontSize: 14 }} color="text.secondary" >
                        contributors
                    </Typography>
                </div>

                <CustomizedProgressBar data={data} height={7} />

            </CardContent>

        </Card>
    );
}