import CoreModules from "../../shared/CoreModules";

const ThemeSlice = CoreModules.createSlice({
    name: 'theme',
    initialState: {
        hotTheme: {
            palette: {
                black:'#000000',
                mode: 'light',
                primary: {
                    main: '#ffffff',
                    contrastText: '#44546a',
                    lightblue: '#99e6ff',
                    primary_rgb: 'rgb(255, 255, 255,0.8)'
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
                    info_rgb: 'rgb(44,48,56,0.2)'

                },
                text: {
                    secondary: '#2C3038',
                },
                loading: {
                    skeleton_rgb: 'rgb(112, 67, 67,0.1)'
                },
                mapFeatureColors: {
                    //blue
                    ready: '#008099',
                    ready_rgb: 'rgb(0, 128, 153,0.4)',
                    locked_for_mapping: '#0063cc',
                    locked_for_mapping_rgb: 'rgb(0, 99, 204,0.4)',
                    mapped: '#161969',
                    mapped_rgb: 'rgb(22, 25, 105,0.4)',
                    locked_for_validation: '#3d1c97',
                    locked_for_validation_rgb: 'rgb(61, 28, 151,0.4)',
                    //green
                    validated: '#006600',
                    validated_rgb: 'rgb(0, 102, 0,0.4)',
                    //yellow
                    // invalidated: '#ffff00',
                    invalidated: '#ffcc00',
                    invalidated_rgb: 'rgb(255, 204, 0,0.4)',
                    //brown
                    bad: '#704343',
                    bad_rgb: 'rgb(112, 67, 67,0.4)',
                    split: '#704343',
                    split_rgb: 'rgb(112, 67, 67,0.4)',
                }

            },
            typography: {
                //default font family changed to BarlowMedium
                fontSize: 16,
                // fontFamily: 'ArchivoMedium',
                fontFamily: 'BarlowMedium',
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
                subtitle3: {
                    fontFamily: 'BarlowMedium',
                    fontSize: 15
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
