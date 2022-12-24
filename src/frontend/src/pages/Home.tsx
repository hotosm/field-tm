import React from "react";
import ExploreProjectCard from "../utilities/Card";
import Box from '@mui/material/Box';

const Home = () => {



    return (
        <div>
            <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex', flexDirection: 'row', justifyContent: 'center',width:'100%'} }}>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
            </Box>

            <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex', flexDirection: 'row', justifyContent: 'center',width:'100%'} }}>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
                <ExploreProjectCard maxWidth={280}/>
            </Box>


            <Box sx={{ display: { xs: 'flex', md: 'none', flexDirection: 'column', justifyContent: 'center',width:'100%'}}}>
                <ExploreProjectCard maxWidth={450}/>
                <ExploreProjectCard maxWidth={450}/>
            </Box>
        </div>
    )

}

export default Home;