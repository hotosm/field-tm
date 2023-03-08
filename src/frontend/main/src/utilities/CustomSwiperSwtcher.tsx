import React from "react";
import AssignmentIcon from '@mui/icons-material/Assignment';
import { Button } from "@mui/material";
import { useSelector } from "react-redux";
const CustomSwiperSwitcher = ({ mode, data, selected, index, onClick, loading }) => {
    const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
    switch (mode) {
        case 'task':
            return (
                <Button
                    key={index}
                    endIcon={<AssignmentIcon key={index} />}
                    color="error"
                    id={data.id}
                    disabled={loading}
                    style={{
                        fontSize: defaultTheme.typography.htmlFontSize,
                        fontFamily: defaultTheme.typography.h3.fontFamily,
                    }}
                    onClick={onClick}
                    variant={selected == data.id ? 'contained' : 'outlined'}
                >
                    {`Task #${data.id}`}
                </Button>
            )
        default:
            return (<div key={index}></div>);
    }
}

export default CustomSwiperSwitcher;
