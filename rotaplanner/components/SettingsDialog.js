import React from 'react';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { names } from '../lib/names';
import { ConfigForm } from './ConfigForm';
import { constraints, deleteDeep, setDeep, store, updateDeep } from '../lib/store';
import { Accordion, AccordionActions, AccordionDetails, AccordionSummary } from '@mui/material';

export function SettingsDialog() {   
    const [open, setOpen] = React.useState(false);
    const [formSpecs, setFormSpecs] = React.useState({})
    const [constraints, updateConstraint] = React.useReducer(
        (state, action) => {
            console.log({state,action})
            switch (action.type) {
                case 'loading':
                    return { ...state, loadingStatus: 'loading' }
                case 'loaded':
                    return {
                        ...state,
                        loadingStatus: 'loaded'
                    }
                case 'reset':
                    return {
                        ...state,
                        loadingStatus:'no'
                    }
                case 'delete':
                    return deleteDeep(state,['constraints',action.constraintName,action.id])
                case 'update':
                    return setDeep(state,
                        ['constraints', action.constraintName,action.id],
                        action.constraintParams)
                case 'addAnother':
                    return setDeep(state,['constraints',action.constraintName,Math.random().toString(36).slice(2)],{})
                case 'replaceAll':
                    return {...state,constraints:action.constraintdefs,loadingStatus:'loaded'}
                case 'updateField':
                    return setDeep(state,['constraints',action.constraintName,action.id,action.name],action.value)
            }
        }, { loadingStatus: 'no', constraints: {} })
    
    React.useEffect(() => {
        fetch('/backend/constraintdefs').then(
            response => response.json()
        ).then(
            formdef => {
                setFormSpecs(formdef)
            }
        )
    }, [open])
    React.useEffect(() => {
        if (constraints.loadingStatus == 'no') {
            updateConstraint({type:'loading'})
            fetch('/backend/constraints').then(
                response=>response.json()
            ).then(
                constraintdefs => {
                            updateConstraint({ type: 'replaceAll', constraintdefs })
                })
        }
    },[constraints.loadingStatus])
    const handleClickOpen = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };
    const handleReset = () => {
        updateConstraint({type:'reset'})
    }
    const handleSave = () => {
        fetch('/backend/constraints', {
            headers: { 'accept': 'application/json' },
            method: 'post',
            body: JSON.stringify(constraints.constraints)
        }).then(() => {
            handleClose()
        })
    }

    return (
        <div>
            <Button variant="outlined" onClick={handleClickOpen}>
                Settings...
            </Button>
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Settings</DialogTitle>
                <DialogContent>
                    {constraints.loadingStatus=='loading'?'loading...':null}
                    {Object.entries(constraints.constraints).map(([constraintName, constraintdef]) =>
                        (formSpecs[constraintName]?.definition?.length ?? 0) == 0 ? null : 
                            <Accordion>
                                <AccordionSummary>{formSpecs[constraintName].name}</AccordionSummary>
                                <AccordionDetails>
                        {Object.entries(constraintdef).map(([id, constraint],i,arr) =>
                        ((
                            <Card key={id} sx={{ padding: 1, margin: 1 }}>
                                <ConfigForm id={id} constraintName={constraintName} formSpec={formSpecs[constraintName].definition}
                                    values={constraint} update={updateConstraint} lastOne={arr.length==1}
                                />
                            </Card>)))}</AccordionDetails>
                                <AccordionActions>
                            {(formSpecs[constraintName].definition.length > 1) ? <Button sx={{ margin: 1 }}
                                variant='outlined'
                                size='small'
                                onClick={() => updateConstraint({ type: 'addAnother', constraintName })}>
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
