import { Box } from "@mui/material";
import React from "react";

const CustomizedProgressBar = ({ height }) => {
    return (

        <div className="progress" style={{ marginTop: '2%', height }}>
            <div className="progress-bar " role="progressbar" style={{ width: '50%', backgroundColor: '#007acc' }}></div>
            <div className="progress-bar " role="progressbar" style={{ width: '30%', backgroundColor: '#2db92d' }} ></div>
            <div className="progress-bar " role="progressbar" style={{ width: '20%', backgroundColor: '#ff3333' }}></div>
        </div>


    )
}

export default CustomizedProgressBar;