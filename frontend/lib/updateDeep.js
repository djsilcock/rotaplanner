const sentinel = Symbol();

export function getDeep(obj, path, defaultValue = sentinel) {
    if (typeof path == 'string') {
        return getDeep(obj, path.split('.'), defaultValue);
    }

    if (path.length == 0) {
        return obj;
    }

    if ((typeof obj != 'object') || !(path[0] in obj)) {
        if (defaultValue == sentinel) {
            throw 'not found';
        }
        return defaultValue;
    }

    return getDeep(
        obj[path[0]],
        path.slice(1),
        defaultValue);
}

export function setDeep(obj, path, value) {
    if (typeof path == 'string') {
        return setDeep(obj, path.split('.'), value);
    }
    obj = obj || {};
    if (path.length == 0) {
        return value;
    }
    const newvalue = setDeep(
        obj[path[0]],
        path.slice(1),
        value);
    if (obj[path[0]] === newvalue)
        return obj;
    return {
        ...obj,
        [path[0]]: newvalue
    };
}

export function updateDeep(obj, path, updater) {
    return setDeep(obj, path, updater(getDeep(obj, path, null)));
}

export function deleteDeep(obj, path) {
    if (typeof path == 'string') {
        return deleteDeep(obj, path.split('.'));
    }
    if (path.length == 0) {
        throw 'no path given';
    }
    const sentinel2 = Symbol();
    if (getDeep(obj, path, sentinel2) == sentinel2)
        return obj;

    return updateDeep(
        obj,
        path.slice(0, -1),
        (deepValue) => {
            const newValue = {};
            for (let key in deepValue) {
                if (key != path.slice(-1)[0]) {
                    newValue[key] = deepValue[key];
                }
            }
            return newValue;
        });
}
