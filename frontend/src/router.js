import Vue from 'vue'
import VueRouter from 'vue-router'

import Leadboard from '@/components/Leaderboard.vue'

const routes = [
  { path: '*', component: Leadboard }
]

Vue.use(VueRouter)
const router = new VueRouter({
  scrollBehavior (to, from, savedPosition) { return { x: 0, y: 0 } },
  mode: 'history',
//  base: 'leaderboard',
  routes
})

export default router
