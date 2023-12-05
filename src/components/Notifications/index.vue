<script lang="ts">
import Icon from '@/components/Icon/index.vue'
import './index.scss'

export default {
  name: 'Notifications',
  components: { Icon },
  computed: {
    notifications() {
      return this.$store.getters.getNotifications
    }
  },
  methods: {
    closeNotification(id: string) {
      this.$store.commit('removeNotification', id)
    },
    iconName(type: string) {
      const icons = {
        info: 'info',
        success: 'success',
        warning: 'attention',
        error: 'attention'
      }

      return icons[type as keyof typeof icons]
    }
  }
}
</script>

<template>
  <div class="Notifications">
    <div
      v-for="notification in notifications"
      class="NotificationsItem"
      :class="['NotificationsItem_' + notification.type]"
      :key="notification.id"
    >
      <span class="NotificationsItemImage" :class="['NotificationsItemImage_' + notification.type]">
        <Icon class="NotificationsItemImageIcon" :name="iconName(notification.type)" />
      </span>
      <div class="NotificationsItemData">
        <div class="NotificationsItemTitle">{{ notification.title }}</div>
        <div v-if="notification.text" class="NotificationsItemText">{{ notification.text }}</div>
      </div>
      <span class="NotificationsItemClose" @click="closeNotification(notification.id)">
        <Icon class="NotificationsItemCloseIcon" name="close" />
      </span>
    </div>
  </div>
</template>
