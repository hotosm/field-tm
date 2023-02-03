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

const ActivitiesPanel = ({ viewMode }) => {
    return (
        <Box>
            <Grid container columns={{ xs: 2, sm: 3, md: 7 }}>
                {Array.from(Array(10)).map((_, index) => (
                    <Grid xs={2} p={0.5} sm={1} md={1} mt={1} key={index}>
                        <BasicCard
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
        </Box>
    )
}

export default ActivitiesPanel;