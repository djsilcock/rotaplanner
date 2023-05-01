
function useRemoteApi(){
    return {
        dutyClick({name,date,session}){window.pywebview.api.duty_click(name,date,session)},
        output(out){pywebview.api.output(out)}
    }
}

export default useRemoteApi