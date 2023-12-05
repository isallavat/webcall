import 'virtual:svg-icons-register'
import './assets/scss/main.scss'

import { createApp } from 'vue'
import App from './App.vue'
import store from '@/store'

const app = createApp(App)

app.use(store)

app.mount('#app')
