import { SelectPicker } from 'rsuite';
import React, { useState } from 'react';
import '../styles/home.css'
import CoreModules from '../shared/CoreModules';

const CustomSelect = ({ data }) => {
    const defaultTheme: any = CoreModules.useSelector<any>(state => state.theme.hotTheme)
    const [styles, setStyles] = useState({
        backgroundColor: 'white',
        color: defaultTheme.palette.info['main'],
        fontFamily: defaultTheme.typography.subtitle2.fontFamily,
        fontSize: defaultTheme.typography.h3.fontSize,
    })

    const onMouseEnter = (event) => {
        const element: any = document.getElementById(`${event.target.id}`);
        element.style.backgroundColor = 'whitesmoke';
        element.style.color = defaultTheme.palette.error['main']
    }

    const onMouseLeave = (event) => {
        const element: any = document.getElementById(`${event.target.id}`);
        element.style.backgroundColor = 'white';
        element.style.color = defaultTheme.palette.info['main']
    }

    return (
        <SelectPicker data={data}
            style={styles}
            color='red'
            searchable={false}
            onEnter={onMouseEnter}
            onExit={onMouseLeave} />
    )
}

export default CustomSelect;
