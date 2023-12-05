import { v4 as uuidv4 } from 'uuid'
import { createStore } from 'vuex'

export type TNotification = {
  id?: string
  title: string
  type?: string
  text?: string | JSX.Element
}

export type StoreState = {
  notifications: TNotification[]
}

export default createStore({
  state: {
    notifications: []
  },
  mutations: {
    addNotification(state: StoreState, notification: TNotification) {
      notification.id = notification.id || uuidv4()
      notification.type = notification.type || 'info'

      state.notifications.push(notification)
    },
    removeNotification(state: StoreState, id: string) {
      state.notifications = state.notifications.filter(
        (notification: TNotification) => notification.id !== id
      )
    }
  },
  actions: {
    addNotification({ commit }, notification: TNotification) {
      commit('addNotification', notification)

      setTimeout(() => {
        commit('removeNotification', notification.id)
      }, 5000)
    }
  },
  getters: {
    getNotifications: (state: StoreState) => state.notifications
  }
})
