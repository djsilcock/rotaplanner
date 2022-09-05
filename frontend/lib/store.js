import { legacy_createStore as createStore,applyMiddleware} from 'redux'
import React from 'react'
import { io } from 'socket.io-client'
import {Provider} from 'react-redux'



function remoteReducer(state = { value: 0 }, action) {
  if (typeof action=='undefined') return {}
  switch (action.type) {
    case 'remote/replaceState':
      return action.newState
    default:
      return state
  }
}
function makeRemoteMiddleware(){
  const socket=io()
  return store=>next=>{
    const decodeAndDispatch=action=>{
      console.log('remote action')
      console.log(action)
      action && next(action)}
    let handler=socket.on('remoteAction',decodeAndDispatch)
    socket.on('connect',()=>socket.emit('reset_state',decodeAndDispatch))
    return action=>{
      socket.emit('dispatch',action,decodeAndDispatch)
}
}}

const store = createStore(remoteReducer,window.initialData ?? {daysArray:[]},applyMiddleware(makeRemoteMiddleware()))

export function ReduxProvider({children}){
  return <Provider store={store}>{children}</Provider>
}