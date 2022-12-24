import { Dropdown, ButtonToolbar } from 'rsuite';
import React from 'react';

const SizeDropdown = props => (
    <Dropdown  color='red'   appearance="ghost" {...props}>
        <Dropdown.Item>Urgent Projects</Dropdown.Item>
        <Dropdown.Item>Active Projects</Dropdown.Item>
        <Dropdown.Item>New Projects</Dropdown.Item>
        <Dropdown.Item>Old Projects</Dropdown.Item>
        <Dropdown.Item>Easy Projects</Dropdown.Item>
        <Dropdown.Item>Challenging Projects</Dropdown.Item>
    </Dropdown>
);
const DropdownUtl = ({toolBarStyle,btnStyle,text,size}) => {
    return (
        <ButtonToolbar  style={toolBarStyle}>
            <SizeDropdown  style={btnStyle} title={text}  size={size} />
        </ButtonToolbar>
    )
}

export default DropdownUtl;