import {createRoot} from 'react-dom/client'
import { configureStore } from '@reduxjs/toolkit'
import {Component,gridSlice} from './component'
import { Provider } from 'react-redux'

el=document.getElementById('root')
root=createRoot(el)
window.store = configureStore({
  reducer: {grid:gridSlice.reducer},
})

root.render(
  <Provider store={store}>
    <Component />
  </Provider>
)
