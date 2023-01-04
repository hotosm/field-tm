import { Box } from "@mui/material";
import React from "react";

const CustomizedProgressBar = ({ height, data }) => {

    return (

        <div className="progress" style={{ marginTop: '2%', height }}>
            <div className="progress-bar " role="progressbar" style={{ width: `${100 / (data.total_tasks / data.tasks_mapped)}%`, backgroundColor: '#007acc' }}></div>
            <div className="progress-bar " role="progressbar" style={{ width: `${100 / (data.total_tasks / data.tasks_validated)}%`, backgroundColor: '#2db92d' }} ></div>
            <div className="progress-bar " role="progressbar" style={{ width: `${100 / (data.total_tasks / data.tasks_bad)}%`, backgroundColor: '#ff3333' }}></div>
        </div>


    )
}

export default CustomizedProgressBar;