import * as React from 'react';
import Button from '@mui/material/Button';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import Stack from '@mui/material/Stack';

export default function OutlinedButton({ style, icon, text, color, variant }) {
    return (
        <Button variant={variant} color={color == undefined ? 'warning' : color} style={style} startIcon={icon}>
            {text}
        </Button>
    );
}