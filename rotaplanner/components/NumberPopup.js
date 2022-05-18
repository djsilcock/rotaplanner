import React from 'react';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormGroup from '@mui/material/FormGroup';
import { Stack } from '@mui/material';
import { Hyperlink } from './Hyperlink';

export function NumberPopup({ name, value: defaultValue, onChange }) {
    const [open, setOpen] = React.useState(false);
    const [value, setValue] = React.useState(defaultValue);
    React.useEffect(() => { setValue(defaultValue); }, [defaultValue, open]);
    const handleChange = React.useCallback((evt) => { setValue(evt.target.value); }, [setValue]);
    const handleClose = () => { setOpen(false); };
    return <>
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>Enter Value:</DialogTitle>
            <DialogContent>
                <Stack>
                    <FormGroup>
                        <TextField value={value} onChange={handleChange} type='number' />
                    </FormGroup>
                </Stack>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => { handleClose(); onChange({ name, value }); }}>OK</Button>
                <Button onClick={() => { handleClose(); }}>Cancel</Button>
            </DialogActions>s
        </Dialog>
        <Hyperlink onClick={() => { setOpen(true); }}>{defaultValue}</Hyperlink>
    </>;
}
