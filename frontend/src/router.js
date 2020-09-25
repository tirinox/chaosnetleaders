import Vue from 'vue'
import VueRouter from 'vue-router'

import Leadboard from '@/components/Leaderboard.vue'
import Help from '@/components/Help.vue'

const routes = [
  { path: '/', component: Leadboard },
  { path: '/help', component: Help }
]

Vue.use(VueRouter)
const router = new VueRouter({
  scrollBehavior () { return { x: 0, y: 0 } },
  mode: 'history',
  routes
})

export default router
