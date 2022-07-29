import React from 'react';
import { DateFieldPopup } from './DateFieldPopup';
import { MultiSelectPopup } from './MultiSelectPopup';
import { TextNode } from './TextNode';
import { NumberPopup } from './NumberPopup';
import { MenuPopup } from './MenuPopup';
import { DateRangeDialog } from './DateRangeDialog';

export function GenericComponent({ component, allValues,value, displayif,dispatch, ...spec }) {
    const Component = {
        text: TextNode,
        multiselect: MultiSelectPopup,
        select: MenuPopup,
        date: DateFieldPopup,
        number: NumberPopup,
        daterange:DateRangeDialog
    }[component];
    if (displayif) {
        /* eslint-disable-next-line no-new-func*/
        try {
            const fxn = new Function('values', 'return ' + displayif)
            if (!fxn(allValues)) return ' '
        }catch(e){
            console.warn('uncaught error',e)
        }
    }
    return <Component value={value} onChange={dispatch} {...spec} />;
}
