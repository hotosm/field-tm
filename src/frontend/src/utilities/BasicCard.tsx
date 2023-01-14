import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CustomizedText from './CustomizedText';
import { Stack } from '@mui/material';



export default function BasicCard({ title, subtitle, content, variant, contentProps, headerStatus, width }) {

    return (
        <Card sx={{ width: width }} variant={variant}>
            <CardContent {...contentProps}>
                {headerStatus && <Stack direction={'column'} spacing={1}>
                    <CustomizedText {...title} />
                    <CustomizedText {...subtitle} />
                </Stack>}
                {content}
            </CardContent>
        </Card>
    );
}