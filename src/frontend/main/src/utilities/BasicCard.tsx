import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { Stack, Typography } from '@mui/material';



export default function BasicCard({ title, subtitle, content, variant, contentProps, headerStatus }) {

    return (
        <Card sx={{ width: '100%' }} variant={variant}>
            <CardContent {...contentProps}>
                {headerStatus && <Stack direction={'column'} spacing={1}>
                    {/* <Typography
                        variant='h1'
                    >
                        {title}
                    </Typography>
                    <Typography
                        variant='h2'
                    >
                        {subtitle}
                    </Typography> */}
                </Stack>}
                <Box style={{ display: 'flex', flexDirection: 'column', justifyContent: 'left' }}>
                    {content}
                </Box>
            </CardContent>
        </Card>
    );
}