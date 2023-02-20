import { Box, Grid, Paper } from "@mui/material";
import React from "react";
import { experimentalStyled as styled } from '@mui/material/styles';
import BasicCard from "../../utilities/BasicCard";
import Activities from "./Activities";

const Item = styled(Paper)(({ theme }) => ({
    backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
    ...theme.typography.body2,
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.secondary,
}));

const ActivitiesPanel = () => {
    return (
        <Box>
            <Grid container item columns={{ xs: 2, sm: 3, md: 7 }}>
                <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 1, sm: 3, md: 4, lg: 6, xl: 7 }}>
                    {Array.from(Array(10)).map((_, index) => (
                        <Grid item xs={1} sm={1} md={1} lg={1} xl={1} key={index}>
                            <BasicCard
                                key={index}
                                title={{}}
                                subtitle={{}}
                                contentProps={{}}
                                variant={'elevation'}
                                headerStatus={false}
                                content={<Activities />}
                            />
                        </Grid>
                    ))}
                </Grid>
            </Grid>
        </Box>
    )
}

export default ActivitiesPanel;