import * as React from 'react';
import CoreModules from '../shared/CoreModules';

export default function BasicCard({ title, subtitle, content, variant, contentProps, headerStatus }) {

    return (
        <CoreModules.Card sx={{ width: '100%' }} variant={variant}>
            <CoreModules.CardContent {...contentProps}>
                {headerStatus && <CoreModules.Stack direction={'column'} spacing={1}>
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
                </CoreModules.Stack>}
                <CoreModules.Box style={{ display: 'flex', flexDirection: 'column', justifyContent: 'left' }}>
                    {content}
                </CoreModules.Box>
            </CoreModules.CardContent>
        </CoreModules.Card>
    );
}
