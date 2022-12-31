import { Dropdown, ButtonToolbar } from 'rsuite';
import React, { useState } from 'react';
import enviroment from '../enviroment';


const DropdownUtl = ({ toolBarStyle, btnStyle, text, size, names }) => {
    const [styles, setStyles] = useState({
        backgroundColor: 'white',
        color: enviroment.sysBlackColor,
        fontFamily: 'BarlowMedium'
    })

    const onMouseEnter = (event) => {
        const element: any = document.getElementById(`${event.target.id}`);
        element.style.backgroundColor = 'whitesmoke';
        element.style.color = `${enviroment.sysRedColor}`


    }

    const onMouseLeave = (event) => {
        const element: any = document.getElementById(`${event.target.id}`);
        element.style.backgroundColor = 'white';
        element.style.color = `${enviroment.sysBlackColor}`

    }
    return (
        <Dropdown style={toolBarStyle} menuStyle={btnStyle} title={text} size={size} appearance='ghost' color='red'>
            {
                names.map((value, index) => {
                    return (
                        <Dropdown.Item key={index} id={index} style={styles} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}>{value}</Dropdown.Item>
                    )
                })
            }
        </Dropdown>
    )
}

export default DropdownUtl;