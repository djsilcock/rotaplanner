import React from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { StaticDatePicker } from '@mui/x-date-pickers/StaticDatePicker';
import { format, formatISO, parseISO } from 'date-fns';
import { Hyperlink } from './Hyperlink';

export function DateFieldPopup({ value: defaultValue, name, onChange }) {
    const [open, setOpen] = React.useState(false);
    const [value, setValue] = React.useState<string>(defaultValue)
    React.useEffect(() => { setValue(defaultValue); }, [open, defaultValue]);
    const handleClose = () => { setOpen(false); };
    return <>
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>Settings</DialogTitle>
            <DialogContent>
                <input type='date' value={value} onChange={e=>setValue(e.target.value)}/>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => { setValue(undefined); }}>Clear</Button>
                <Button onClick={() => { onChange({ name, value}); handleClose(); }}>Accept</Button>
                <Button onClick={handleClose}>Cancel</Button>
            </DialogActions>
        </Dialog>
        <Hyperlink onClick={() => { setOpen(true); }}>{defaultValue ? format(parseISO(defaultValue), 'd/M/yy') : '(no date)'}</Hyperlink>
    </>;
}
