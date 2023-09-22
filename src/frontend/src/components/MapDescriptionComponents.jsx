import React from 'react';
import CustomizedMenus from '../utilities/CustomizedMenus';
import CoreModules from '../shared/CoreModules';

const MapDescriptionComponents = ({ type, state, defaultTheme }) => {
  const descriptionData = [
    {
      value: 'Descriptions',
      element: <CoreModules.Typography align="center">{state.projectInfo.description}</CoreModules.Typography>,
    },
    // {
    //   value: "Instructions",
    //   element: (
    //     <CoreModules.Typography align="center">
    //       {state.projectInfo.location_str}
    //     </CoreModules.Typography>
    //   ),
    // },
    // {
    //   value: "Legends",
    //   element: (
    //     <MapLegends
    //       direction={"column"}
    //       defaultTheme={defaultTheme}
    //       spacing={1}
    //       iconBtnProps={{ disabled: true }}
    //       valueStatus
    //     />
    //   ),
    // },
  ];
  return (
    <CoreModules.Stack
      sx={{
        display: 'flex',
        flexDirection: 'row',
        width: '100%',
        mt: 1,
        pl: 2.5,
        pr: 2.5,
      }}
    >
      <CoreModules.Stack
        width={'100%'}
        p={1}
        spacing={type == 's' ? 1 : type == 'xs' ? 1 : 3}
        direction={type == 's' ? 'column' : type == 'xs' ? 'column' : 'row'}
        justifyContent={'center'}
      >
        {descriptionData.map((data, index) => {
          return (
            <CustomizedMenus
              key={index}
              btnName={data.value}
              btnProps={{
                style: {
                  //overidding style
                  backgroundColor: 'white',
                  fontFamily: defaultTheme.typography.h1.fontFamily,
                  fontSize: 16,
                },
                color: 'primary',
                sx: { boxShadow: 2 },
              }}
              element={data.element}
            />
          );
        })}
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};

export default MapDescriptionComponents;
