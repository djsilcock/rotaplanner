import { deleteDeep, setDeep, updateDeep } from "../lib/updateDeep";
import {createAction, createReducer} from '@reduxjs/toolkit'

export const actions={
    delete:createAction('constraints/delete'),
    updateField:createAction('constraints/update'),
    addAnother:createAction('constraints/newConstraint'),
    resetConstraintSettings:createAction('constraints/reset')
}

export const constraintsReducer=createReducer({},(builder)=>{
    builder.addCase(actions.delete,(state,action)=>
        deleteDeep(state, 
            [action.payload.constraintName, action.payload.id]))
    builder.addCase(actions.updateField,(state,action)=>
        setDeep(state, [action.constraintName, action.id, action.name], action.value)
)
}
    )

