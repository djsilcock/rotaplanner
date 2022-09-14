import {configureStore,combineReducers} from '@reduxjs/toolkit'
import { remoteReduxMiddleware, remoteReduxWrapReducer } from 'remote-redux'
import {immutableJSONPatch} from 'immutable-json-patch'
import React from 'react'
import { io } from 'socket.io-client'
import {Provider} from 'react-redux'

function reducer(state = { value: 0 }, action) {
  if (typeof action=='undefined') return {}
  return state
}

const reducer = combineReducers({
  config:combineReducers({})
})

const isRemoteAction = (action) => {
  return action.type.includes('remote/')
}

const socket = io()
const makeRequest=(state, action, callback) => {    
  socket.emit(action.type.slice(7), state, action,(patches)=>callback(immutableJSONPatch(state,patches)));
  };

const store = configureStore({
  reducer: remoteReduxWrapReducer(reducer),
  middleware: remoteReduxMiddleware(makeRequest,isRemoteAction,reducer),
  preloadedState: window.initialData ?? { daysArray: [] }
})
socket.on("connect", () => socket.emit("reset_state", decodeAndDispatch));
socket.on("dispatch", store.dispatch);

export function ReduxProvider({children}){
  return <Provider store={store}>{children}</Provider>
}