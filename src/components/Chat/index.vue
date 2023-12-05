<script lang="ts">
import Icon from '@/components/Icon/index.vue'
import UniInput from '@/components/UniInput/index.vue'
import { formatDate } from '@/helpers'
import type { TMessage } from '@/types/global'
import './index.scss'

export default {
  name: 'Chat',
  props: ['id', 'user', 'socket'],
  components: { Icon, UniInput },
  data() {
    return {
      messages: [] as TMessage[],
      messageText: ''
    }
  },
  mounted() {
    this.socket
      .on('call:messages', (eventData: { id: string; messages: TMessage[] }) => {
        this.messages = eventData.messages
      })
      .on('call:message', (eventData: { id: string; message: TMessage }) => {
        this.messages.push(eventData.message)
        setTimeout(() => this.scrollToBottom(), 1)
      })

    this.socket.send('call:messages', { id: this.id })
  },
  computed: {
    isSubmitDisabled() {
      return !this.messageText.trim()
    }
  },
  methods: {
    formatMessageTime(timestamp: number) {
      return formatDate(timestamp, 'HH:mm')
    },

    scrollToBottom() {
      const messagesList = this.$refs.messagesList as HTMLDivElement
      messagesList.scrollTop = messagesList.scrollHeight
    },

    handleTextKeydown(event: KeyboardEvent) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault()
        this.handleSubmit()
      }
    },

    handleSubmit() {
      if (!this.isSubmitDisabled) {
        this.socket.send('call:message', { id: this.id, text: this.messageText.trim() })
        this.messageText = ''
      }
    }
  }
}
</script>

<template>
  <div class="Chat">
    <div class="ChatSpacer"></div>
    <div class="ChatMessages" ref="messagesList">
      <div v-for="message in messages" class="ChatMessagesItem" :key="message.id">
        <div class="ChatMessagesItemName">
          {{ message.user_name }}
        </div>
        <div class="ChatMessagesItemText">{{ message.text }}</div>
        <div class="ChatMessagesItemTime">{{ formatMessageTime(message.created_at) }}</div>
      </div>
    </div>
    <div class="ChatBar">
      <UniInput
        class="ChatBarInput"
        type="area"
        placeholder="Write a message"
        v-model="messageText"
        @keydown="handleTextKeydown"
      />
      <button
        class="ChatBarButton"
        :class="{ '--active': !isSubmitDisabled }"
        :disabled="isSubmitDisabled"
        @click="handleSubmit"
      >
        <Icon class="ChatBarButtonIcon" name="send" />
      </button>
    </div>
  </div>
</template>
