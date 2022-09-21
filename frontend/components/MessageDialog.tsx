import React from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSelector,useDispatch } from 'react-redux';
import isEqual from 'lodash/isEqual';

const selectors={
    messagePopup:(state)=>(state.messagePopup || [])
}
const actions={
    dismissMessage:()=>({type:'remote/dismissPopup'})
}

export function MessageDialog() {
    const dispatch=useDispatch()
    const message = useSelector(selectors.messagePopup,isEqual)
    const handleOK = () => dispatch(actions.dismissMessage())
    
    return (
        <div>
            <Dialog open={!!message[0]} onClose={handleOK}>
                <DialogTitle>Message</DialogTitle>
                <DialogContent>
                     <ReactMarkdown remarkPlugins={[remarkGfm]}>{message[0]}</ReactMarkdown>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleOK}>OK</Button>
                </DialogActions>
            </Dialog>
        </div>
    );
}