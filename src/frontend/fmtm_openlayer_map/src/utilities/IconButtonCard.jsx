import { Stack } from '@mui/system'
import React from 'react'

export default function IconButtonCard({ element, style, radius }) {
    return (

        <Stack
            style={style}
            width={50}
            height={50}
            borderRadius={radius == undefined ? 55 : radius}
            boxShadow={2}
            justifyContent={'center'}
        >
            {element}
        </Stack>
    )
}
