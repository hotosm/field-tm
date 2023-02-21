import { Stack } from "@mui/material";
import React from "react";
import { GridLoader } from "react-spinners";

const MapLoader = () => {
    const override = {
        display: "block",
        margin: "0 auto",
        borderColor: "red",

    };
    return (
        <Stack
            left={'50%'}
            top={'50%'}
            position={'absolute'}
            justifyContent={'center'}
        >
            <GridLoader color={'red'} loading={false} cssOverride={override} size={30} />
        </Stack>
    );
}

export default MapLoader;