import React from "react";
import AssignmentIcon from '@mui/icons-material/Assignment';
import { Button } from "@mui/material";
import { useSelector } from "react-redux";
const CustomSwiperSwitcher = ({ mode, data, selected, key }) => {
    const defaultTheme: any = useSelector<any>(state => state.theme.hotTheme)
    switch (mode) {
        case 'task':
            return (
                <Button
                    key={key}
                    endIcon={<AssignmentIcon />}
                    color="error"
                    style={{
                        fontSize: defaultTheme.typography.htmlFontSize,
                        fontFamily: defaultTheme.typography.h3.fontFamily,
                    }}
                    variant={selected.count == data.count ? 'contained' : 'outlined'}
                >
                    {`Task #${data.count}`}
                </Button>
            )
        default:
            return null;
    }
}

export default CustomSwiperSwitcher;