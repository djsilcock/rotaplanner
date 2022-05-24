import React from 'react';
import MenuItem from '@mui/material/MenuItem';
import { Menu } from '@mui/material';
import { Hyperlink } from './Hyperlink';

export function MenuPopup({ value='', options, name, onChange }) {
    const ref = React.useRef(null);
    const [open, setOpen] = React.useState(false);
    
    const handleClose = React.useCallback(() => { setOpen(false); }, []);
    const handleMenuItemClick = React.useCallback((value) => {
        onChange({ name, value });
        handleClose();
    }, [name, handleClose, onChange]);
    return <><Menu
        id="lock-menu"
        anchorEl={ref.current}
        open={open}
        onClose={handleClose}
        MenuListProps={{
            'aria-labelledby': 'lock-button',
            role: 'listbox',
        }}
    >
        {options.map((option, index) => (
            <MenuItem
                key={option}
                selected={option.toLowerCase() == value.toLowerCase()}
                onClick={() => { handleMenuItemClick(option); }}
            >
                {option}
            </MenuItem>
        ))}
    </Menu>
        <Hyperlink ref={ref} onClick={() => { setOpen(true); }}>{value||'nothing selected'}</Hyperlink></>;
}
