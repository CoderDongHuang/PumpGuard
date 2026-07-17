import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'GlobalMap', component: () => import('./views/GlobalMap.vue') },
  { path: '/station/:id', name: 'StationDetail', component: () => import('./views/StationDetail.vue') },
  { path: '/pump/:id', name: 'PumpDetail', component: () => import('./views/PumpDetail.vue') },
  { path: '/workorders', name: 'WorkOrders', component: () => import('./views/WorkOrders.vue') },
  { path: '/alerts', name: 'Alerts', component: () => import('./views/Alerts.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
