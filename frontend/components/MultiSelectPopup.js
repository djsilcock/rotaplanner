import React from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Stack from '@mui/material/Stack';
import { Hyperlink } from './Hyperlink';

export function MultiSelectPopup({ name, options, value: suppliedDefaultValue, onChange }) {
    const [defaultValue, setDefaultValue] = React.useState(() => (typeof suppliedDefaultValue == 'undefined') ? [] : suppliedDefaultValue)
    React.useEffect(()=>{if (typeof suppliedDefaultValue !="undefined"){setDefaultValue(suppliedDefaultValue)}},[suppliedDefaultValue])
    const normalisedDefaultValue = React.useMemo(() => defaultValue.map(v => v.toLowerCase()), [defaultValue])
    const optionsDict = React.useMemo(() => {
        const opt = {}
        options.forEach(option => {
            opt[option.toLowerCase()]=option
        })
        return opt
    },[options])
    const displayValue = React.useMemo(() => {
        if (normalisedDefaultValue.length==0) return '(none)'
        return normalisedDefaultValue.map(opt => optionsDict[opt]).join(',')
    }, [normalisedDefaultValue, optionsDict])
    
    const [open, setOpen] = React.useState(false);
    const initReducer = React.useCallback(() => {
        const state = {};
        try {
            for (let opt in optionsDict) {
                state[opt] = normalisedDefaultValue.includes(opt);
            }
        } catch (exc) {
            console.warn('an error occurred here')
        }
        return state;
    }, [optionsDict, normalisedDefaultValue]);
    const [value, dispatch] = React.useReducer(
        (state, action) => {
            if (action.reset) {
                return initReducer();
            }
            return { ...state, [action.value]: action.checked };
        }, undefined, initReducer);
    
    React.useEffect(() => {
        dispatch({ reset: true });
    }, [defaultValue, open]);
    const handleOK = () => {
        handleClose()
        onChange({
            name,
            value: options.filter((opt) => value[opt.toLowerCase()])
        });
    }
    const handleCancel = () => {
        dispatch({ reset: true })
        handleClose();
    }
    const handleClose = () => {
        setOpen(false);
    };
    const handleClick = React.useCallback((evt) => {
        dispatch(evt.target);
    }, [dispatch]);
    try {
        return <>
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Settings</DialogTitle>
                <DialogContent>
                    <Stack>
                        <FormGroup>
                            {Object.keys(optionsDict).map(
                                option => <FormControlLabel
                                    key={option}
                                    control={<Checkbox onClick={handleClick} value={option} checked={value[option]} />}
                                    label={optionsDict[option]} />)}
                        </FormGroup>
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleOK}>OK</Button>
                    <Button onClick={handleCancel}>Cancel</Button>
                </DialogActions>
            </Dialog>
            <Hyperlink onClick={() => { setOpen(true); }}>{displayValue}</Hyperlink>
        </>;
    } catch (e) {
        console.warn('an error occured while rendering')
        return null
    }
}
