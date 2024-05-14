let backend = {
    by_name(){ return {}},
    get_duty_for_staff_and_date(staff,day){return {}},
    get_table_config(){return {}},
    set_activity(self,name,dutydate,activity) {return true},
    del_activity(self,name,dutydate,activity) {return true},
    get_demand_templates_for_week(date){return {}}
    
}

window.api={}

const { promise, resolve} = Promise.withResolvers()
window.addEventListener('pywebviewready', () => { console.log('backend ready');resolve() })


const backendProxy = new Proxy(backend, {
    get(target, property) {
//        console.log(`accessed ${property}`)
        return async (...args) => {
//            console.log(`invoking ${property}`)
            return promise.then(
                () => window.pywebview.api[property](...args)
            )
        }
    }
})
export default backendProxy
