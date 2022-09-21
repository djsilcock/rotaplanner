import React from 'react';
import { DateFieldPopup } from './DateFieldPopup';
import { MultiSelectPopup } from './MultiSelectPopup';
import { TextNode } from './TextNode';
import { NumberPopup } from './NumberPopup';
import { MenuPopup } from './MenuPopup';
import { DateRangeDialog } from './DateRangeDialog';
export function GenericComponent({ component, value,onChange,...spec }) {
    const Component = {
        text: TextNode,
        multiselect: MultiSelectPopup,
        select: MenuPopup,
        date: DateFieldPopup,
        number: NumberPopup,
        daterange:DateRangeDialog
    }[component];
    
    return <Component value={value} onChange={onChange} {...spec} />;
}
