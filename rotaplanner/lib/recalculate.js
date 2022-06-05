import { store, message, constraints } from '../../rotaplanner/lib/store';
import { setDuty } from './setDuty';

export const recalculate = async (store, dispatch) => {

    dispatch({ type: 'message', message: 'recalculating' })
    console.log(store)
    const it = makeTextFileLineIterator('/backend/recalculate', {
        headers: { 'accept': 'application/json' },
        method: 'post',
        body: JSON.stringify(store)
    });
    for await (let line of it) {
        const action = JSON.parse(line);
        switch (action.type) {
            case 'result':
                dispatch({ type: 'result', result: action.result });
                break;
            case 'duty':
                dispatch({ dutyType: action.dutyType, shift: action.shift, name: action.name, day: action.day });
                break;
            case 'info':
                dispatch({ type: 'message', message: action.message });
                break;
            case 'progress':
                dispatch({ type: 'message', message: `Working... ${action.objective} to go after ${action.time}s` });
                break;
            case 'solveStatus':
                dispatch({type:'message',message:`Solution: ${action.statusName}`});
                break;
            default:
                console.log(JSON.parse(line));
        }
    }
};

async function* makeTextFileLineIterator(fileURL, fetchparams) {
    const utf8Decoder = new TextDecoder("utf-8");
    let response = await fetch(fileURL, fetchparams);
    let reader = response.body.getReader();
    let { value: chunk, done: readerDone } = await reader.read();
    chunk = chunk ? utf8Decoder.decode(chunk, { stream: true }) : "";
    let re = /\r\n|\n|\r/gm;
    let startIndex = 0;

    for (; ;) {
        let result = re.exec(chunk);
        if (!result) {
            if (readerDone) {
                break;
            }
            let remainder = chunk.substr(startIndex);
            ({ value: chunk, done: readerDone } = await reader.read());
            chunk = remainder + (chunk ? utf8Decoder.decode(chunk, { stream: true }) : "");
            startIndex = re.lastIndex = 0;
            continue;
        }
        yield chunk.substring(startIndex, result.index);
        startIndex = re.lastIndex;
    }
    if (startIndex < chunk.length) {
        // last line didn't end in a newline char
        yield chunk.substr(startIndex);
    }
}
