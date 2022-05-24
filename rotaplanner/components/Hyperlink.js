import React from 'react';
import { Box } from '@mui/system';

export const Hyperlink = React.forwardRef(function Hyperlink({ onClick, children }, ref) {
    return <> <Box
        component='span'
        sx={{
            fontWeight:'bold',
            color: 'blue',
            cursor: 'pointer',
            '&:hover': {
                textDecoration: 'underline',
                backgroundColor: '#f7f7ff'
            }
        }}><span ref={ref} onClick={onClick}>{children}</span></Box> </>;
}
);
