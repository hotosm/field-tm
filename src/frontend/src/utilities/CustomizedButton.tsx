import * as React from 'react';
import Button from '@mui/material/Button';

export default function CustomizedButton({ style, icon, text, color, variant }) {
    return (
        <Button variant={variant} color={color == undefined ? 'warning' : color} style={style} startIcon={icon}>
            {text}
        </Button>
    );
}