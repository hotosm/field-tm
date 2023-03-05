import { Stack } from '@mui/system'
import React from 'react'

export default function IconButtonCard({ element, style }) {
    return (

        <Stack
            style={style}
            width={50}
            height={50}
            borderRadius={55}
            boxShadow={2}
            justifyContent={'center'}
        >
            {element}
        </Stack>
    )
}
