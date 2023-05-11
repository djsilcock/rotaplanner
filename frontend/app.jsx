import {createRoot} from 'react-dom/client'
import { configureStore } from '@reduxjs/toolkit'
import {Component,gridSlice} from './component'
import { Provider } from 'react-redux'

el=document.getElementById('root')
root=createRoot(el)
window.store = configureStore({
  reducer: {grid:gridSlice.reducer},
})
if (window?.pywebview?.api){
  console.log('ready')
  window.pywebview.api.refresh_data()
}else{
  console.log('not ready yet')
  window.addEventListener('pywebviewready',()=>{console.log('ready now');window.pywebview.api.refresh_data()})
}
window.store.do_dispatch=(action)=>{console.log(action);window.store.dispatch(action)}
root.render(
  <Provider store={store}>
    <Component />
  </Provider>
)
