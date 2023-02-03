import { Box } from "@mui/material";
import React from "react";
import { useSelector } from "react-redux";


const CustomizedProgressBar = ({ height, data }) => {
    const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
    return (

        <div className="progress" style={{ marginTop: '2%', height }}>
            <div
                className="progress-bar "
                role="progressbar"
                style={{
                    width: `${100 / (data.total_tasks / data.tasks_mapped)}%`,
                    backgroundColor: defaultTheme.palette.info['main']
                }}>

            </div>

            <div
                className="progress-bar "
                role="progressbar"
                style={{
                    width: `${100 / (data.total_tasks / data.tasks_validated)}%`,
                    backgroundColor: defaultTheme.palette.success['main']
                }} >

            </div>
            <div
                className="progress-bar "
                role="progressbar"
                style={{
                    width: `${100 / (data.total_tasks / data.tasks_bad)}%`,
                    backgroundColor: defaultTheme.palette.error['main']
                }}></div>
        </div>


    )
}

export default CustomizedProgressBar;