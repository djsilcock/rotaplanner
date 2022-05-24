import { observable } from 'mobx';
import { names } from './names'
export const store = observable.map();
export const constraints = new Map()
export const message = observable.box('');

const sentinel=Symbol()

export function getDeep(obj, path,defaultValue=sentinel) {
    if (typeof path == 'string') {
        return getDeep(obj, path.split('.'), defaultValue)
    }
    
    if (path.length == 0) {
        return obj
    }

    if ((typeof obj != 'object')||!(path[0] in obj)) {
        if (defaultValue == sentinel) {
            throw 'not found'
        }
        return defaultValue
    }
    
    return getDeep(
        obj[path[0]],
        path.slice(1),
        defaultValue)
}

export function setDeep(obj, path, value) {
    if (typeof path == 'string') {
        return setDeep(obj, path.split('.'), value)
    }
    obj = obj || {}
    if (path.length == 0) {
        return value
    }
    const newvalue = setDeep(
        obj[path[0]],
        path.slice(1),
        value)
    if (obj[path[0]] === newvalue) return obj
    return {
        ...obj,
        [path[0]]: newvalue
    }
}

export function updateDeep(obj, path, updater) {
    return setDeep(obj, path, updater(getDeep(obj, path,null)))
}

export function deleteDeep(obj, path) {
    if (typeof path == 'string') {
        return deleteDeep(obj, path.split('.'))
    }
    if (path.length == 0) {
      throw 'no path given'  
    }
    const sentinel2=Symbol()
    if (getDeep(obj,path,sentinel2)==sentinel2) return obj
    
    return updateDeep(
        obj,
        path.slice(0, -1),
        (deepValue) => {
        const newValue = {}
        for (let key in deepValue) {
            if (key != path.slice(-1)[0]) {
                newValue[key]=deepValue[key]
            }
        }
        return newValue
    })
}


export function dutyReducer(state, action) {
    if (typeof state == 'undefined') {
        return {
            duties: names.reduce(
                (prev, curr) => ({ ...prev, [curr]: { DAYTIME: {}, ONCALL: {} } }),
                {}), message: ''
        }
    }
    if (action.type == 'message') {
        return {...state,message:action.message}
    }
    if (action.type == 'statistic') {
        console.log(action)
    }
    const {dutyType,name,shift,day}=action
    switch (dutyType) {
        case 'CLEAR':
                return setDeep(state, ['duties',name, shift, day], undefined)
        case 'DEFINITE_ICU':
        case 'ICU':
                return names.reduce((intstate,name2) => (
                    updateDeep(intstate, ['duties',name2, shift, day], (val) => {
                        if (name == name2) {
                            return dutyType
                        }
                        if (['ICU', 'DEFINITE_ICU'].includes(val)) {
                            return undefined
                        }
                        return val
                    }
                    )),state)
                
            
        //eslint-disable-next-line no-fallthrough
        default:
            return setDeep(state,['duties',name,shift,day],dutyType)
    }
}
