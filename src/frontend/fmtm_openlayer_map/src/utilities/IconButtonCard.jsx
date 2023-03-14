import React from 'react'
import CoreModules from 'fmtm/CoreModules';
export default function IconButtonCard({ element, style, radius }) {
    return (

        <CoreModules.Stack
            style={style}
            width={50}
            height={50}
            borderRadius={radius == undefined ? 55 : radius}
            boxShadow={2}
            justifyContent={'center'}
        >
            {element}
        </CoreModules.Stack>
    )
}
