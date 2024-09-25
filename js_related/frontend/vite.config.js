import { defineConfig } from 'vite'
import solid from 'vite-plugin-solid'

export default defineConfig({
  plugins: [solid()],
  server:{
    proxy:{
      '/api':'http://localhost:8080'
    }
  },
  build:{manifest:true}
})
