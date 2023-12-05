<script setup lang="ts">
import { ref } from 'vue'
import { useStore } from 'vuex'
import Call from '@/components/Call/index.vue'
import Icon from '@/components/Icon/index.vue'
import Notifications from '@/components/Notifications/index.vue'
import UniInput from '@/components/UniInput/index.vue'
import { makeRequest, copyToClipboard } from '@/helpers'

import './App.scss'

const url = new URL(window.location.href)
const baseUrl = import.meta.env.BASE_URL
const store = useStore()
const isUserForm = ref(false)
const isCallSession = ref(false)
const callId = ref(url.searchParams.get('session_id') || undefined)
const user = ref()
const username = ref()
let token = localStorage.getItem('token')

function create() {
  if (token) {
    getProfile()
      .then(() => createCall())
      .catch(() => (isUserForm.value = true))
  } else if (username.value) {
    createUser().then(() => createCall())
  } else {
    isUserForm.value = true
  }
}

function join() {
  if (token) {
    getProfile()
      .then(() => (isCallSession.value = true))
      .catch(() => (isUserForm.value = true))
  } else if (username.value) {
    createUser().then(() => (isCallSession.value = true))
  } else {
    isUserForm.value = true
  }
}

function getProfile() {
  return new Promise((resolve, reject) => {
    makeRequest('/api/me')
      .then((response) => {
        user.value = response
        resolve(response)
      })
      .catch((err) => {
        token = null
        localStorage.removeItem('token')
        reject(err)
      })
  })
}

function createUser() {
  return makeRequest('/api/users', {
    method: 'POST',
    body: { name: username.value }
  }).then((response) => {
    isUserForm.value = false
    username.value = undefined
    user.value = response
    token = response.token as string
    localStorage.setItem('token', token)
  })
}

function createCall() {
  return makeRequest('/api/calls', {
    method: 'POST'
  }).then((response) => {
    callId.value = response.id
    changeUrl(response.id)
    store.dispatch('addNotification', {
      type: 'success',
      title: 'Call created'
    })
  })
}

function changeUrl(id: string) {
  const url = new URL(window.location.href)
  url.searchParams.set('session_id', id)
  history.pushState({}, '', url)
}

function copyLink() {
  if (callId.value) {
    const url = new URL(window.location.origin)
    url.searchParams.set('session_id', callId.value)
    const div = document.createElement('div')
    div.style.position = 'absolute'
    div.style.right = '100%'
    div.innerHTML = url.href

    document.body.appendChild(div)

    copyToClipboard(div)
      .then(() => {
        document.body.removeChild(div)
        store.dispatch('addNotification', {
          type: 'success',
          title: 'Link copied to clipboard'
        })
      })
      .catch(() => {
        document.body.removeChild(div)
      })
  }
}
</script>

<template>
  <div class="App">
    <h1 class="AppTitle">WebCall</h1>
    <a :href="baseUrl" aria-label="home">
      <img class="AppLogo" src="@/assets/img/call.png" alt="" />
    </a>
    <div class="AppButtons">
      <button v-if="callId" class="AppButton" @click="join">Join call</button>
      <button v-else class="AppButton" @click="create">New call</button>
    </div>
    <div class="AppFooter">
      <div v-if="callId" class="AppSession">
        <div class="AppSessionLabel">Session ID:</div>
        <div class="AppSessionValue" @click="copyLink">
          <span>{{ callId }}</span> <Icon class="AppSessionIcon" name="copy" />
        </div>
      </div>
      <form v-if="isUserForm" class="AppUserForm" @submit.prevent="createUser">
        <UniInput v-model="username" placeholder="Write your name" />
      </form>
    </div>
    <Call v-if="isCallSession" :id="callId" :user="user" @close="isCallSession = false" />
    <Notifications />
  </div>
</template>
