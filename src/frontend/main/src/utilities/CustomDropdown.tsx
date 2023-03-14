import { Dropdown } from 'rsuite';
import React, { useState } from 'react';
import '../styles/home.css'
import CoreModules from '../shared/CoreModules';

const CustomDropdown = ({ toolBarStyle, text, size, names, appearance, color }) => {
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
        <Dropdown
            menuStyle={{ width: '100%' }}
            style={toolBarStyle}
            title={text}
            size={size}
            appearance={appearance}
            color={color}
        >
            {
                names.map((value, index) => {
                    return (
                        <Dropdown.Item
                            key={index}
                            id={index}
                            style={styles}
                            onMouseEnter={onMouseEnter}
                            onMouseLeave={onMouseLeave}>
                            {value}
                        </Dropdown.Item>
                    )
                })
            }
        </Dropdown>
    )
}

export default CustomDropdown;
