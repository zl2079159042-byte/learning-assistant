import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/home/HomeView.vue')
  },
  {
    path: '/learn',
    name: 'LearnList',
    component: () => import('@/views/learn/LearnListView.vue')
  },
  {
    path: '/learn/:id',
    name: 'LearnDetail',
    component: () => import('@/views/learn/LearnDetailView.vue')
  },
  {
    path: '/chat',
    name: 'ChatList',
    component: () => import('@/views/chat/ChatListView.vue')
  },
  {
    path: '/chat/:id',
    name: 'ChatDetail',
    component: () => import('@/views/chat/ChatDetailView.vue')
  },
  {
    path: '/document',
    name: 'DocumentList',
    component: () => import('@/views/document/DocumentListView.vue')
  },
  {
    path: '/document/:id',
    name: 'DocumentDetail',
    component: () => import('@/views/document/DocumentDetailView.vue')
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/knowledge/KnowledgeView.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/history/HistoryView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
