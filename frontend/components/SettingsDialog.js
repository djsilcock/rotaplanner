import React from 'react';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { ConfigForm } from './ConfigForm';
import { deleteDeep, setDeep, updateDeep } from "../lib/updateDeep";
import Accordion from '@mui/material/Accordion';
import AccordionActions from '@mui/material/AccordionActions';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';

import { useDispatch, useSelector } from 'react-redux';
import isEqual from 'lodash/isEqual';


//selectors
const selectors = {
    constraints: (state) => state?.config?.constraints || {}
}
const actions = {
    saveConstraints: () => ({ type: 'remote/saveConstraints'})
}


/*expected shape of state:
 state.config.constraints=
 []
 */
export function SettingsDialog() {
    const [open, setOpen] = React.useState(false);
    const serverConstraints = useSelector(selectors.constraints, isEqual)
    const dispatch = useDispatch()
    const [constraints, updateConstraint] = React.useReducer(
        (state, action) => {
            switch (action.type) {
                case 'reset':
                    return {
                        ...state,
                        constraints: serverConstraints,
                    }
                case 'delete':
                    return deleteDeep(state, ['constraints', action.constraintName, action.id])
                case 'update':
                    return setDeep(state,
                        ['constraints', action.constraintName, action.id],
                        action.constraintParams)
                case 'addAnother':
                    return setDeep(state, ['constraints', action.constraintName, Math.random().toString(36).slice(2)], {})
                case 'replaceAll':
                    return { ...state, constraints: action.constraintdefs }
                case 'updateField':
                    return setDeep(state, ['constraints', action.constraintName, action.id, action.name], action.value)
            }
        }, { constraints: serverConstraints })
    console.log({ formSpecs, serverConstraints, constraints })

    const handleClickOpen = () => {
        updateConstraint({ type: 'reset' })
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };
    const handleReset = () => {
        updateConstraint({ type: 'reset' })
    }
    const handleSave = () => {
        dispatch(actions.saveConstraints(constraints.constraints))
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
                                            form={form} values={values} update={updateConstraint} lastOne={arr.length == 1}
                                            />
                                        </Card>)))}</AccordionDetails>
                                <AccordionActions>
                                    {addButton ? <Button sx={{ margin: 1 }}
                                        variant='outlined'
                                        size='small'
                                        onClick={() => updateConstraint({ type: 'addAnother', constraintType })}>
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
