import React from 'react';
import CoreModules from '../shared/CoreModules';
export default function IconButtonCard({ element, style, radius }) {
  return (
    <CoreModules.Stack
      style={style}
      width={40}
      height={40}
      borderRadius={radius == undefined ? 55 : radius}
      boxShadow={2}
      justifyContent={'center'}
    >
      {element}
    </CoreModules.Stack>
  );
}
