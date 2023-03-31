import React, { useEffect } from "react";
import '../styles/home.css'
import CoreModules from "../shared/CoreModules";
import { useLocation, useNavigate } from 'react-router-dom';

const NewPage = () => {
    const location = useLocation();

    // history.push(path);
    // const defaultTheme = CoreModules.useSelector(state => state.theme.hotTheme)
    // // const state:any = useSelector<any>(state=>state.project.projectData)
    // // console.log('state main :',state)

    // const { type } = windowDimention();
    // //get window dimension


    // const theme = CoreModules.useSelector(state => state.theme.hotTheme)
    // useEffect(() => {
    //     dispatch(HomeSummaryService(`${enviroment.baseApiUrl}/projects/summaries?skip=0&limit=100`))
    //     //creating a manual thunk that will make an API call then autamatically perform state mutation whenever we navigate to home page
    // }, [])


    return (
        <CoreModules.Box sx={{ px: 25, py: 6 }}>
            <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row' }}>
                <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'column', width: '51%' }}>
                    <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', gap: 1 }}>
                        {/* Project Details SideBar Button for Creating Project */}
                        <CoreModules.Button
                            variant="contained"
                            color="error"
                        >
                            Monitoring
                        </CoreModules.Button>

                        {/* END */}

                        {/* Upload Area SideBar Button for uploading Area page  */}
                        <CoreModules.Button
                            variant="contained"
                            color="error"
                        >
                            Convert
                        </CoreModules.Button>
                        <CoreModules.Button
                            variant="contained"
                            color="error"
                        >
                            Download CSV
                        </CoreModules.Button>
                        {/* END */}
                    </CoreModules.Stack>
                    <CoreModules.Box component="h4" sx={{ background: 'gray', mt: 5 }}>Lorem ipsum dolor sit amet consectetur adipisicing elit. Consequuntur tempore deleniti et, exercitationem minus nostrum aliquid perferendis ut numquam neque dicta dolores, beatae ipsa, eius quis odit cum quidem fugiat.Lorem ipsum dolor sit amet consectetur adipisicing elit. Consequuntur tempore deleniti et, exercitationem minus nostrum aliquid perferendis ut numquam neque dicta dolores, beatae ipsa, eius quis odit cum quidem fugiatLorem ipsum dolor sit amet consectetur adipisicing elit. Consequuntur tempore deleniti et, exercitationem minus nostrum aliquid perferendis ut numquam neque dicta dolores, beatae ipsa, eius quis odit cum quidem fugiatLorem ipsum dolor sit amet consectetur adipisicing elit. Consequuntur tempore deleniti et, exercitationem minus nostrum aliquid perferendis ut numquam neque dicta dolores, beatae ipsa, eius quis odit cum quidem fugiat</CoreModules.Box>
                </CoreModules.Stack>
                <CoreModules.Box sx={{ width: '100%', ml: 6, border: '1px solid green' }}></CoreModules.Box>
            </CoreModules.Stack >

        </CoreModules.Box >
    )

}

export default NewPage;
