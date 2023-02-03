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
                },
                error: {
                    //hot red
                    main: '#d73f3e',
                },
                success: {
                    //hot blue
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