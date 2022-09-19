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

import { useDispatch} from 'react-redux';

import { actions } from './settingsRedux';
import { api } from '../lib/store';

const {
    useGetConstraintConfigQuery,
    useResetConstraintConfigMutation,
    useSaveConstraintsMutation } = api

export function SettingsDialog() {
    const [open, setOpen] = React.useState(false);
    //const constraints = useSelector(selectors.constraints, isEqual)
    const {data:constraints} = useGetConstraintConfigQuery()
    const [resetConstraints] = useResetConstraintConfigMutation()
    const [saveConstraints]=useSaveConstraintsMutation()
    const dispatch = useDispatch()
    const handleClickOpen = () => {
        resetConstraints()
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };
    const handleReset = () => {
        resetConstraints()
    }
    const handleSave = () => {
        saveConstraints()
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
                    {constraints.constraints.map(({type,title,rules,addButton}) =>
                            <Accordion key={type}>
                                <AccordionSummary>{title}</AccordionSummary>
                                <AccordionDetails>
                                {rules.map(({ id, ...values }, i, arr) =>
                                    ((
                                        <Card key={id} sx={{ padding: 1, margin: 1 }}>
                                            <ConfigForm id={id} constraintName={type} 
                                            values={values} lastOne={arr.length == 1}
                                            />
                                        </Card>)))}</AccordionDetails>
                                <AccordionActions>
                                    {addButton ? <Button sx={{ margin: 1 }}
                                        variant='outlined'
                                        size='small'
                                        onClick={() => dispatch(actions.addAnother(type))}>
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



