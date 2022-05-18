
import React from 'react';
import TableCell from '@mui/material/TableCell';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import { store } from '../lib/store';
import { setDuty } from '../lib/setDuty';

export const Cell=React.memo(function Cell({ name, day, dutyType,daytimeValue,oncallValue,setDuty }) {
    const props1 = {
        ICU: ['blue', 'ICU?'],
        DEFINITE_ICU: ['green', 'ICU'],
        LEAVE: ['gray', 'Leave'],
        NOC: ['orange', 'NOC'],
    }[daytimeValue] || ['gray', '-'];
    const props2 = {
        ICU: ['navy', 'ICU?'],
        DEFINITE_ICU: ['darkgreen', 'ICU'],
        LEAVE: ['gray', 'Leave'],
        NOC: ['orange', 'NOC'],
    }[oncallValue] || ['gray', '-'];
    const handleClick = (shift) => () => { setDuty({ dutyType, shift, name, day }); };
    return <TableCell style={{ border: 'solid 1px' }} title={`${name} ${day}`}>
        <ButtonGroup
            orientation="vertical"
            aria-label="vertical outlined button group"
            size='small'
        ><Button style={{ border: 'none', width: '100%', height: '100%', color: props1[0] }} onClick={handleClick('DAYTIME')}>{props1[1]}</Button>
            <Button style={{ border: 'none', width: '100%', height: '100%', color: props2[0] }} onClick={handleClick('ONCALL')}>{props2[1]}</Button></ButtonGroup>
    </TableCell>;
})
