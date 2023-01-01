import React from "react";
import ExploreProjectCard from "../components/home/ExploreProjectCard";
import Box from '@mui/material/Box';
import { Container } from "@mui/material";
import windowDimention from "../customHooks/WindowDimension";
import BasicPagination from "../utilities/BasicPagination";



const Home = () => {


    const { windowSize, type } = windowDimention();
    //get window dimension

    //home project card display algorith but it will make more sense in real data scenario
    let a = '01234567891234';
    let ds = type == 'lg' ? 5 : type == 'xl' ? 7 : type == 'md' ? 4 : type == 'sm' ? 3 : type == 's' ? 2 : 1
    let dta = Array.of(...a)
    let rowsDta = Array.of(...a)
    let rows: number = dta.length % ds == 0 ? Math.floor(dta.length / ds) : Math.floor(dta.length / ds) + 1

    let lgOut = new Array(rows).fill(0)
    let lgIn = new Array(ds).fill(0)

    return (

        <Container disableGutters={false} maxWidth={false} >
            {
                lgOut.map((value, index) => {
                    return (
                        <Box key={index} sx={{ flexGrow: 1, display: { xs: 'flex', sm: 'flex', lg: 'flex', xl: 'flex', md: 'flex', flexDirection: 'row', justifyContent: 'left', width: '100%' } }}>
                            {
                                dta.length % lgIn.length == 0 ?
                                    lgIn.map((val, index) => {
                                        let value = rowsDta.shift()
                                        return (
                                            <ExploreProjectCard data={value} length={ds} key={index} />
                                        )
                                    }) :
                                    index + 1 != lgOut.length ?
                                        lgIn.map((val, index) => {
                                            let value = rowsDta.shift()
                                            return (
                                                <ExploreProjectCard data={value} length={ds} key={index} />
                                            )
                                        }) :
                                        new Array(dta.length % lgIn.length).fill(0).map((val, index) => {
                                            let value = rowsDta.shift()
                                            return (
                                                <ExploreProjectCard length={ds} data={value} key={index} />
                                            )
                                        })
                            }
                        </Box>
                    )

                })



            }
            <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', marginTop: '1.5%' }}>
                <BasicPagination count={10} color="primary" variant="outlined" />
            </Box>

        </Container>

    )

}

export default Home;