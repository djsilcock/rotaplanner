import {useQuery,useQueryClient} from '@tanstack/react-query'
import {useFormContext, type Resolver,type SubmitHandler,type RegisterOptions} from 'react-hook-form'
import React from 'react'
function resolveOrSubmit(data,url) {
    return fetch(url, {
        method: 'POST',
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
        .then(result => {
            if (result.ok) return result.json()
            throw 'error'}
            )
}


function getFormDef({queryKey}){
    return fetch(`/constraints/${queryKey[1]}/config`).then(r=>r.json())
}

interface ConstraintConfig<T extends Record<string,(string|number)>>{
    defaultValues:T;
    validate:Resolver<T>;
    submit:SubmitHandler<T>;
}
function useConstraintConfig<F extends Record<string,(string|number)>>(configKey:string):ConstraintConfig<F>{
    const {data}=useQuery({queryKey:['constraintConfig',configKey],suspense:true,queryFn:getFormDef})
    const client=useQueryClient()
    const {defaultValues,submitUrl,validateUrl}=data
    const validate=React.useCallback((values)=>resolveOrSubmit(values,validateUrl),[validateUrl])
    const submit=React.useCallback(values=>resolveOrSubmit(values,submitUrl)
        .then(()=>client.invalidateQueries({queryKey:['constraintConfig']})),[submitUrl,client]
    )
    return {defaultValues,validate,submit}

}
interface InputProps{
    name:string;
    options?:RegisterOptions;
}
function Input(props:(InputProps&{inputType:string})){
    const {name,options,inputType}=props
    const {register}=useFormContext()
    return <input type={inputType} {...register(name,options)}></input>    
}

function TextInput(props:InputProps){
    return <Input inputType="text" {...props}/>
}
function NumberInput(props:InputProps){
    const options={valueAsNumber:true}
    return <Input inputType="number" options={options}
}



export {useConstraintConfig}