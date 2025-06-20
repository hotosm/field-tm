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
        UNLOCKED_TO_MAP: 'rgba(255,255,255, 0.3)',
        LOCKED_FOR_MAPPING: 'rgba(0, 128, 153, 0.3)',
        UNLOCKED_TO_VALIDATE: 'rgba(173, 230, 239, 0.8)',
        LOCKED_FOR_VALIDATION: 'rgb(252,236,164,0.3)',
        UNLOCKED_DONE: 'rgba(64, 172, 140, 0.3)',
      },
      entityStatusColors: {
        ready: 'rgba(156,154,154,1)',
        opened_in_odk: 'rgb(252,236,164,1)',
        survey_submitted: 'rgba(64,172,140,1)',
        marked_bad: 'rgba(250,17,0,1)',
        validated: 'rgba(0,123,255,1)',
      },
      lineEntityStatusColors: {
        ready: 'rgba(156,154,154,0.8)',
        opened_in_odk: 'rgb(252,236,164,1)',
        survey_submitted: 'rgba(64,172,140,0.8)',
        marked_bad: 'rgba(250,17,0,0.8)',
        validated: 'rgba(0,123,255,0.8)',
      },
    },
    statusTextTheme: {
      UNLOCKED_TO_MAP: '#a3a2a2',
      LOCKED_FOR_MAPPING: '#097085',
      UNLOCKED_TO_VALIDATE: '#64cfe3',
      LOCKED_FOR_VALIDATION: '#C5BD0A',
      UNLOCKED_DONE: '#44c9a2',
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
      fontFamily: 'Barlow',
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
      h5: {
        fontFamily: 'BarlowLight',
        fontSize: 14,
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
