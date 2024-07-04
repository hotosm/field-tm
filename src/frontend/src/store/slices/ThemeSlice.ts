import { createSlice } from '@reduxjs/toolkit';

type themeStateType = {
  hotTheme: any;
};

const initialState: themeStateType = {
  hotTheme: {
    palette: {
      black: '#000000',
      mode: 'light',
      primary: {
        main: '#ffffff',
        contrastText: '#44546a',
        lightblue: '#99e6ff',
        primary_rgb: 'rgb(255, 255, 255,0.8)',
      },
      error: {
        //hot red
        main: '#d73f3e',
        purple: '#ff3399',
      },
      success: {
        //hot blue
        //green in regular
        main: '#459ca0',
        contrastText: '#2C3038',
      },
      warning: {
        //hot yellow
        main: '#f9a61e',
        contrastText: '#2C3038',
      },
      grey: {
        //hot grey and light
        main: '#a5a5a5',
        light: '#f0efee',
        contrastText: '#2C3038',
      },
      info: {
        //hot dark
        main: '#44546a',
        contrastText: '#2C3038',
        info_rgb: 'rgb(44,48,56,0.2)',
      },
      text: {
        secondary: '#2C3038',
      },
      loading: {
        skeleton_rgb: 'rgb(112, 67, 67,0.1)',
      },
      mapFeatureColors: {
        //blue
        ready: 'rgba(255,255,255, 0.5)',
        ready_rgb: 'rgba(255,255,255, 0.5)',
        locked_for_mapping: 'rgba(0, 128, 153, 0.5)',
        locked_for_mapping_rgb: 'rgba(0, 128, 153, 0.5)',
        mapped: 'rgba(173, 230, 239, 0.8)',
        mapped_rgb: 'rgba(173, 230, 239, 0.8)',
        locked_for_validation: 'rgb(252,236,164,0.5)',
        locked_for_validation_rgb: 'rgb(252,236,164,0.5)',
        //green
        validated: 'rgba(64, 172, 140, 0.5)',
        validated_rgb: 'rgba(64, 172, 140, 0.5)',
        //yellow
        // invalidated: '#ffff00',
        invalidated: 'rgb(215,63,62,0.5)',
        invalidated_rgb: 'rgb(215,63,62,0.5)',
        //brown
        bad: 'rgba(216, 218, 228, 0.5)',
        bad_rgb: 'rgba(216, 218, 228, 0.5)',
        split: 'rgb(112, 67, 67,0.5)',
        split_rgb: 'rgb(112, 67, 67,0.5)',
      },
    },
    statusTextTheme: {
      READY: '#a3a2a2',
      LOCKED_FOR_MAPPING: '#097085',
      MAPPED: '#64cfe3',
      LOCKED_FOR_VALIDATION: '#C5BD0A',
      VALIDATED: '#44c9a2',
      INVALIDATED: '#D73F37',
    },
    READY: '#fff',
    LOCKED_FOR_MAPPING: '#fff',
    MAPPED: '#ade6ef',
    LOCKED_FOR_VALIDATION: '#ade6ef',
    VALIDATED: '#40ac8c',
    INVALIDATED: '#fceca4',
    BADIMAGERY: '#d8dae4',
    PRIORITY_AREAS: '#efd1d1',
    typography: {
      //default font family changed to BarlowMedium
      fontSize: 16,
      // fontFamily: 'ArchivoMedium',
      fontFamily: 'BarlowMedium',
      //custom
      htmlFontSize: 18,

      barlowCondensed: {
        fontFamily: 'Barlow Condensed',
        fontSize: '24px',
      },
      caption: {
        fontFamily: 'BarlowBold',
        fontSize: 24,
      },
      // new font size added
      condensed: {
        fontSize: 36,
        fontWeight: 'bold',
      },
      subtitle1: {
        fontFamily: 'BarlowBold',
        fontSize: 24,
        fontWeight: 'bold',
      },
      subtitle2: {
        fontFamily: 'BarlowMedium',
        fontSize: 20,
        fontWeight: 'bold',
      },
      subtitle3: {
        fontFamily: 'BarlowMedium',
        fontSize: 15,
      },
      h1: {
        fontFamily: 'BarlowMedium',
        fontSize: 20,
      },
      h2: {
        fontFamily: 'BarlowMedium',
        fontSize: 16,
      },
      h3: {
        fontFamily: 'BarlowMedium',
        fontSize: 16,
      },
      h4: {
        fontFamily: 'BarlowLight',
        fontSize: 16,
      },
      p: {
        fontFamily: 'Archivo',
        fontSize: 16,
      },
    },
  },
};

const ThemeSlice = createSlice({
  name: 'theme',
  initialState: initialState,
  reducers: {},
});

export const ThemeActions = ThemeSlice.actions;
export default ThemeSlice;
