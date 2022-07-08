import React from 'react';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { useSocket } from '../lib/socketContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function MessageDialog() {
    const socket = useSocket()
    const [message, setMessage] = React.useState([])
    const handleOK = React.useCallback(() => setMessage((state) => state.slice(1)), [setMessage])
    const handleClose = React.useCallback(()=>setMessage([]),[setMessage])
    React.useEffect(() => {
        if (!socket) return
        socket.on('report', ({ message }) => {
            setMessage((state)=>[...state,message])
        })
    }, [socket])
    return (
        <div>
            <Dialog open={!!message[0]} onClose={handleClose}>
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