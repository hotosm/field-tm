import React from 'react'
import CoreModules from '../../shared/CoreModules.js';
// import { SelectPicker } from 'rsuite';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';

const BasemapSelection: React.FC = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)

    const imagerySource = ['OAM', 'Topo'];
    const imagerySourceData = imagerySource.map(
        item => ({ label: item, value: item })
    );
    const mapTiles = ['mbtiles for ODK Collect', 'sqlitedb for Osmand'];
    const mapTilesData = mapTiles.map(
        item => ({ label: item, value: item })
    );
    return (
        <CoreModules.Stack>
            <CoreModules.FormGroup >
                <CoreModules.FormLabel>Imagery Source</CoreModules.FormLabel>
                {/* <SelectPicker data={imagerySourceData}
                    style={{
                        marginBottom: '6%',
                        fontFamily: defaultTheme.typography.h3.fontFamily,
                        fontSize: defaultTheme.typography.h3.fontSize
                    }}
                    searchable={false}
                    onChange={(value) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'xform_title', value }))}
                /> */}
                <CoreModules.FormLabel>Output Type</CoreModules.FormLabel>
                {/* <SelectPicker data={mapTilesData}
                    style={{
                        width: '100%',
                        marginBottom: '6%',
                        fontFamily: defaultTheme.typography.h3.fontFamily,
                        fontSize: defaultTheme.typography.h3.fontSize
                    }}
                    searchable={false}
                // onChange={(value) => dispatch(CreateProjectActions.SetProjectDetails({ key: 'splitting_algorithm', value }))}
                /> */}
                <CoreModules.Button
                    sx={{ mt: 4 }}
                    variant="contained"
                    color="error"
                    // disabled={!fileUpload ? true : false}
                    onClick={() => {
                        navigate('/');
                        // onCreateProjectSubmission();
                    }}
                >
                    Submit
                </CoreModules.Button>
            </CoreModules.FormGroup>
        </CoreModules.Stack>

    )
}


export default BasemapSelection
