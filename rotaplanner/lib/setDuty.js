import { action } from 'mobx';
import { constraints, store } from './store';
import { names } from "./names";

export const setDuty = action(({ dutyType, shift, name, day}) => {
    switch (dutyType) {
        case 'CLEAR':
            store.delete(`${name} ${day} ${shift}`);
            break;
        case 'DEFINITE_ICU':
        case 'ICU':
            names.forEach(name2 => {
                if (name === name2)
                    return;
                if (['DEFINITE_ICU', 'ICU'].includes(store.get(`${name2} ${day} ${shift}`))) {
                    store.delete(`${name2} ${day} ${shift}`);
                }
            });
        //eslint-disable-next-line no-fallthrough
        default:
            if (store.get(`${name} ${day} ${shift}`) === dutyType) {
                store.delete(`${name} ${day} ${shift}`);
            } else {
                store.set(`${name} ${day} ${shift}`, dutyType);
            }
    }
});

export const setConstraint = action((({ id, ...constraint }) => {
    constraints.set(id,constraint)
}))
