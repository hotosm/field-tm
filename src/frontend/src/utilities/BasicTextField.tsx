import * as React from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';

export default function BasicTextField({ label, defaultValue, placeholder, multiline, variant, rows, others }) {
    return (
        <Box
            component="form"
            sx={{
                '& .MuiTextField-root': { m: 1, width: '25ch' },
            }}
            noValidate
            autoComplete="off"
        >

            <TextField
                id="standard-multiline-static"
                label={label}
                multiline={multiline}
                rows={rows}
                defaultValue={defaultValue}
                variant={variant}
                placeholder={placeholder}
                {...others}
            />
        </Box>
    );
}