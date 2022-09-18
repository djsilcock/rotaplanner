import React from 'react';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { ConfigForm } from './ConfigForm';
import Accordion from '@mui/material/Accordion';
import AccordionActions from '@mui/material/AccordionActions';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';

import { useDispatch, useSelector } from 'react-redux';
import isEqual from 'lodash/isEqual';

import { actions } from './settingsRedux';

//selectors
const selectors = {
    constraints: (state) => state?.config?.constraints || {}
}



export function SettingsDialog() {
    const [open, setOpen] = React.useState(false);
    const constraints = useSelector(selectors.constraints, isEqual)
    const dispatch = useDispatch()

    const handleClickOpen = () => {
        dispatch(actions.resetConstraints())
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };
    const handleReset = () => {
        dispatch(actions.resetConstraints())
    }
    const handleSave = () => {
        dispatch(actions.saveConstraints())
        handleClose()
    }
    
    return (
        <div>
            <Button variant="outlined" onClick={handleClickOpen}>
                Settings...
            </Button>
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Settings</DialogTitle>
                <DialogContent>
                    {constraints.constraints.map(({id:constraintType,title, forms,addButton}) =>
                            <Accordion key={constraintType}>
                                <AccordionSummary>{title}</AccordionSummary>
                                <AccordionDetails>
                                {forms.map(({ id, form, values }, i, arr) =>
                                    ((
                                        <Card key={id} sx={{ padding: 1, margin: 1 }}>
                                            <ConfigForm id={id} constraintName={constraintType} 
                                            form={form} values={values} lastOne={arr.length == 1}
                                            />
                                        </Card>)))}</AccordionDetails>
                                <AccordionActions>
                                    {addButton ? <Button sx={{ margin: 1 }}
                                        variant='outlined'
                                        size='small'
                                        onClick={() => dispatch(actions.addAnother(constraintType))}>
                                        Add another
                                    </Button> : null}</AccordionActions>
                            </Accordion>)}


                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose}>Cancel</Button>
                    <Button onClick={handleReset}>Reset</Button>
                    <Button onClick={handleSave}>Save</Button>
                </DialogActions>
            </Dialog>
        </div>
    );
}



