import { createSlice } from "@reduxjs/toolkit";


const ThemeSlice = createSlice({
    name: 'theme',
    initialState: {
        hotTheme: {
            palette: {
                mode: 'light',
                primary: {
                    main: '#ffffff',
                    contrastText: '#44546a',
                    lightblue: '#99e6ff'
                },
                error: {
                    //hot red
                    main: '#d73f3e',
                    purple: '#ff3399'
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
                    "light": '#f0efee',
                    contrastText: '#2C3038',
                },
                info: {
                    //hot dark
                    main: '#44546a',
                    contrastText: '#2C3038',
                },
                text: {
                    secondary: '#2C3038',
                },
                mapFeatureColors: {
                    //blue
                    ready: '#66e5ff',
                    ready_rgb: 'rgb(102, 229, 255,0.2)',
                    locked_for_mapping: '#66afff',
                    locked_for_mapping_rgb: 'rgb(102, 175, 255,0.1)',
                    mapped: '#202395',
                    mapped_rgb: 'rgb(32, 35, 149,0.1)',
                    locked_for_validation: '#7049de',
                    locked_for_validation_rgb: 'rgb(112, 73, 222,0.1)',
                    //green
                    validated: '#006600',
                    validated_rgb: 'rgb(0, 102, 0,0.1)',
                    //yellow
                    invalidated: '#ffff00',
                    invalidated_rgb: 'rgb(255, 255, 0,0.1)',
                    //brown
                    bad: '#dfcaca',
                    bad_rgb: 'rgb(223, 202, 202,0.1)',
                    split: '#dfcaca',
                    split_rgb: 'rgb(223, 202, 202,0.1)'
                }

            },
            typography: {
                //default
                fontSize: 16,
                fontFamily: 'ArchivoMedium',
                //custom
                htmlFontSize: 18,

                caption: {
                    fontFamily: 'BarlowBold',
                    fontSize: 24,
                },
                subtitle1: {
                    fontFamily: 'BarlowBold',
                    fontSize: 20,
                    fontWeight: 'bold'
                },
                subtitle2: {
                    fontFamily: 'BarlowMedium',
                    fontSize: 20
                },
                h1: {
                    fontFamily: 'ArchivoBold',
                    fontSize: 20
                },
                h2: {
                    fontFamily: 'ArchivoMedium',
                    fontSize: 16
                },
                h3: {
                    fontFamily: 'ArchivoRegular',
                    fontSize: 16
                },
                h4: {
                    fontFamily: 'ArchivoLight',
                    fontSize: 16
                },

            },
        }

    },
    reducers: {
        UpdateBrightness(state, action) {
            state.hotTheme = action.payload
        }
    }
})

export const ThemeActions = ThemeSlice.actions;
export default ThemeSlice;