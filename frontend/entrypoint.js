import * as ReactDOM from 'react-dom/client'
import React from 'react'
import App from './pages'

const target = document.getElementById('target')
const root = ReactDOM.createRoot(target)
root.render(<App/>)
console.log('loaded')
