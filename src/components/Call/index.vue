<script lang="ts">
import { useStore } from 'vuex'
import Chat from '@/components/Chat/index.vue'
import Icon from '@/components/Icon/index.vue'
import type { DynamicObject, TAppSocket, TUser } from '@/types/global'
import { initSocket } from '@/helpers'

import './index.scss'

const store = useStore()

export type IMediaStreamTrack = Omit<MediaStreamTrack, 'name'> & {
  name: string
}

export type WsEventData = {
  id: string
  user_id: string
  user?: TUser
  users?: TUser[]
  offer?: RTCSessionDescriptionInit
  answer?: RTCSessionDescriptionInit
  candidate?: RTCIceCandidate
  stream?: MediaStream
  track?: IMediaStreamTrack
}

export default {
  name: 'Call',
  props: ['id', 'user'],
  components: { Icon, Chat },
  data() {
    return {
      controls: { sound: true } as { [key: string]: string | boolean },
      streams: {} as DynamicObject,
      offers: {} as DynamicObject,
      pc: null as RTCPeerConnection | null,
      socket: null as TAppSocket | null,
      isMainVideoEnabled: false,
      windowWidth: window.innerWidth,
      windowResizeTimeout: null as any,
      users: [] as TUser[]
    }
  },
  mounted() {
    this.createPc()
    initSocket()
      .then((socket: TAppSocket) => {
        this.socket = socket
        socket
          .on('call:joined', (eventData: WsEventData) => {
            if (eventData.users) {
              this.users = eventData.users
            }
          })
          .on('call:user-joined', (eventData: WsEventData) => {
            if (eventData.user) {
              this.users.push(eventData.user)
            }

            Object.keys(this.streams).forEach((key) => {
              const stream = this.streams[key]

              if (stream && eventData.user) {
                this.sendPcOffer(eventData.user.id, this.createOfferData(stream))
              }
            })
          })
          .on('call:user-left', (eventData: WsEventData) => {
            this.users = this.users.filter((item) => item.id !== eventData.user?.id)
          })
          .on('call:user-disconnected', (eventData: WsEventData) => {
            this.users = this.users.filter((item) => item.id !== eventData.user?.id)
          })
          .on('call:pc-offer', (eventData: WsEventData) => {
            if (eventData.stream) {
              this.offers[eventData.stream.id] = eventData
            }

            if (eventData.offer && eventData.user) {
              this.handlePcOffer(eventData.user.id, eventData.offer)
            }
          })
          .on('call:pc-answer', (eventData: WsEventData) => {
            eventData.answer && this.handlePcAnswer(eventData.answer)
          })
          .on('call:pc-ice-candidate', (eventData) => {
            this.pc?.addIceCandidate(new RTCIceCandidate(eventData.candidate))
          })

        socket.send('call:join', { id: this.id })
      })
      .catch(() => {
        store.dispatch('addNotification', {
          type: 'error',
          title: "Can't connect to server"
        })
      })
  },
  beforeUnmount() {
    this.handleCallEnded()
  },
  methods: {
    getControlsList() {
      return [
        { name: 'microphone', icon: 'microphone' },
        { name: 'sound', icon: 'sound' },
        { name: 'webcam', icon: 'webcam' },
        { name: 'screen', icon: 'screen' },
        { name: 'chat', icon: 'chat' },
        { name: 'close', icon: 'close' }
      ]
    },

    getUsersTilesLength(length: number) {
      const array = [...Array(10).keys()]
      return (
        array.reduce((accumulator, _, index) => {
          if (length > 1 && this.windowWidth < 400 && this.windowWidth > 300) {
            accumulator = 2
          } else if (length >= index && this.windowWidth < index * 400 && !accumulator) {
            accumulator = index
          }
          return accumulator
        }) || length
      )
    },

    getUserMedia(constraints?: MediaStreamConstraints) {
      return new Promise((resolve, reject) => {
        if (navigator.mediaDevices) {
          navigator.mediaDevices.getUserMedia(constraints).then(resolve).catch(reject)
        } else {
          reject(new Error('getUserMedia not supported'))
        }
      })
    },

    getAudioStream() {
      return new Promise((resolve, reject) => {
        this.getUserMedia({ audio: true, video: false }).then(resolve).catch(reject)
      })
    },

    getVideoStream() {
      return new Promise((resolve, reject) => {
        this.getUserMedia({
          audio: false,
          video: {
            facingMode: 'user',
            width: { ideal: 1920 },
            height: { ideal: 1080 }
          }
        })
          .then(resolve)
          .catch(reject)
      })
    },

    getScreenStream() {
      return new Promise((resolve, reject) => {
        navigator.mediaDevices
          .getDisplayMedia({
            video: true,
            audio: false
          })
          .then(resolve)
          .catch(reject)
      })
    },

    toggleMedia(name: string) {
      const streamId = this.controls[name] as string
      let promise

      if (streamId) {
        const track = this.streams[streamId].getTracks()[0] as IMediaStreamTrack
        track.stop()
        track.dispatchEvent(new Event('ended'))
        delete this.streams[streamId]
        this.pc?.getSenders().forEach((sender) => {
          if (sender.track && sender.track.id === track.id) {
            this.pc?.removeTrack(sender)
          }
        })
        promise = Promise.resolve()
      } else if (name === 'microphone') {
        promise = this.getAudioStream()
      } else if (name === 'webcam') {
        promise = this.getVideoStream()
      } else if (name === 'screen') {
        promise = this.getScreenStream()
      } else {
        promise = Promise.resolve()
      }

      promise
        .then((stream: MediaStream | unknown) => {
          if (stream instanceof MediaStream) {
            const track = stream.getTracks()[0] as IMediaStreamTrack
            track.name = name

            this.streams[stream.id] = stream

            const offerData = this.createOfferData(stream)
            this.pc?.addTrack(track, stream)
            this.sendPcOffer('', offerData)

            if (name === 'screen') {
              this.toggleControl('compact', true)
              track.onended = () => {
                this.toggleControl(name, false)
              }
            } else if (name === 'webcam') {
              const element = document.querySelector(
                `video[data-user-id="${this.user?.id}"]`
              ) as HTMLMediaElement
              this.initMediaElement(name, element, stream)
            }
            this.toggleControl(name, stream.id)
          } else {
            this.toggleControl(name, false)
          }
        })
        .catch((err) => {
          console.log(err)
        })
    },

    initMediaElement(name: string, element: HTMLMediaElement, stream: MediaStream) {
      const track = stream.getTracks()[0]

      if (element.tagName.toLowerCase() === 'video') {
        const userId = element.getAttribute('data-user-id')
        const image = element.parentNode?.querySelector(
          `img[data-user-id="${userId}"]`
        ) as HTMLImageElement

        element.onloadeddata = () => {
          this.setVideoSize()

          if (name === 'screen') {
            this.isMainVideoEnabled = true
          }

          if (image) {
            image.style.display = 'none'
          }
        }

        track.onended = track.onmute = () => {
          element.srcObject = null

          if (name === 'screen') {
            this.isMainVideoEnabled = false
          }

          if (image) {
            image.style.display = 'block'
          }
        }
      }

      element.setAttribute('data-name', name)
      element.srcObject = null
      element.srcObject = stream
      element.autoplay = true
      element.controls = false
    },

    createOfferData(stream: MediaStream) {
      const offerData: { stream: DynamicObject; track: DynamicObject } = { stream: {}, track: {} }
      const track = stream.getTracks()[0] as IMediaStreamTrack

      for (const key in stream) {
        offerData.stream[key] = stream[key as keyof MediaStream]
      }

      for (const key in track) {
        offerData.track[key] = track[key as keyof IMediaStreamTrack]
      }

      return offerData
    },

    toggleControl(name: string, value: string | boolean) {
      this.controls[name] = value
    },

    getVideoDimensions(video: HTMLVideoElement) {
      const parent = video.parentNode as HTMLElement
      const maxHeight = parent.offsetHeight
      const maxWidth = parent.offsetWidth
      let width
      let height

      if (video.videoWidth > video.videoHeight) {
        width = maxWidth
        height = (width / video.videoWidth) * video.videoHeight
      } else {
        height = maxHeight
        width = (height / video.videoHeight) * video.videoWidth
      }

      return {
        width,
        height
      }
    },

    setVideoSize() {
      document.querySelectorAll('video').forEach((element) => {
        const parent = element.parentNode as HTMLElement
        const dimensions = this.getVideoDimensions(element)

        element.style.width = dimensions.width === parent.offsetWidth ? '100%' : 'auto'
        element.style.height = dimensions.height === parent.offsetHeight ? '100%' : 'auto'
      })
    },

    createPc() {
      const configuration: RTCConfiguration = {
        iceServers: [
          {
            urls: 'stun:' + window.location.hostname,
            username: 'webrtc',
            credential: 'turnserver'
          },
          {
            urls: 'turn:' + window.location.hostname,
            username: 'webrtc',
            credential: 'turnserver'
          }
        ]
      }

      this.pc = new RTCPeerConnection(configuration)

      this.pc.onicecandidate = this.handlePcIceCandidate
      this.pc.oniceconnectionstatechange = this.handlePcIceConnectionStateChange
      this.pc.ontrack = this.handlePcTrack
    },

    sendPcOffer(toUserId: string, offerData: any) {
      this.pc?.createOffer().then((offer) => {
        this.pc?.setLocalDescription(offer).then(() => {
          this.socket?.send('call:pc-offer', {
            id: this.id,
            to_user_id: toUserId || undefined,
            ...offerData,
            offer
          })
        })
      })
    },

    sendPcAnswer(toUserId: string) {
      this.pc?.createAnswer().then((answer) => {
        this.pc?.setLocalDescription(answer).then(() => {
          this.socket?.send('call:pc-answer', {
            id: this.id,
            to_user_id: toUserId,
            answer
          })
        })
      })
    },

    handlePcOffer(from: string, offer: RTCSessionDescriptionInit) {
      const description = new RTCSessionDescription(offer)
      this.pc?.setRemoteDescription(description).then(() => {
        this.sendPcAnswer(from)
      })
    },

    handlePcAnswer(answer: RTCSessionDescriptionInit) {
      const description = new RTCSessionDescription(answer)
      this.pc?.setRemoteDescription(description)
    },

    handlePcIceCandidate(event: RTCPeerConnectionIceEvent) {
      if (event.candidate) {
        this.socket?.send('call:pc-ice-candidate', { id: this.id, candidate: event.candidate })
      }
    },

    handlePcIceConnectionStateChange() {
      if (
        this.pc?.iceConnectionState &&
        ['failed', 'disconnected'].includes(this.pc?.iceConnectionState)
      ) {
        // this.handleCallEnded()
      }
    },

    handlePcTrack(event: RTCTrackEvent) {
      const stream = event.streams[0]

      if (this.offers[stream.id]) {
        let element
        const offerData = this.offers[stream.id]
        const track = offerData.track as IMediaStreamTrack

        if (track.name === 'screen') {
          element = document.getElementById('main-video')
        } else if (track.name === 'webcam') {
          element = document.querySelector(`video[data-user-id="${offerData.user.id}"]`)
        } else if (track.name === 'microphone') {
          element = document.querySelector(`audio[data-user-id="${offerData.user.id}"]`)
        }

        this.initMediaElement(track.name, element as HTMLMediaElement, stream)
      }
    },

    handleCallEnded() {
      if (this.socket) {
        this.socket.socket.close()
        this.socket = null
      }

      if (this.pc) {
        this.pc?.close()
        this.pc = null
      }

      if (this.streams) {
        Object.keys(this.streams).forEach((key) => {
          const stream = this.streams?.[key] as MediaStream
          stream.getTracks().forEach((track) => {
            track.stop()
          })
        })
      }

      this.controls = {}
    },

    handleCallControl(name: string) {
      if (name === 'close') {
        this.socket?.send('call:leave', { id: this.id })
        this.handleCallEnded()
        this.$emit('close')
      } else if (['sound', 'chat'].includes(name)) {
        this.toggleControl(name, !this.controls[name])
      } else {
        this.toggleMedia(name)
      }
    },

    handleWindowResize() {
      this.windowResizeTimeout && clearTimeout(this.windowResizeTimeout)
      this.windowResizeTimeout = setTimeout(() => {
        this.windowWidth = window.innerWidth
      }, 300)
    }
  }
}
</script>

<template>
  <div class="Call">
    <div class="CallBody" :class="{ '--compact': !isMainVideoEnabled }">
      <video className="CallVideo" id="main-video" muted />
    </div>
    <div class="CallUsers" :class="{ '--compact': isMainVideoEnabled }">
      <div
        v-for="callUser in users"
        class="CallUsersItem"
        :class="{ '--compact': isMainVideoEnabled }"
        :key="callUser.id"
        :style="{
          width: isMainVideoEnabled ? undefined : `${100 / getUsersTilesLength(users.length)}%`
        }"
      >
        <div className="CallUsersItemTile">
          <video className="CallVideo" muted :data-user-id="callUser.id" />
          <audio className="CallAudio" :muted="!controls.sound" :data-user-id="callUser.id" />
          <img
            className="CallUsersItemImage"
            src="@/assets/img/user.png"
            :data-user-id="callUser.id"
            alt=""
          />
          <div className="CallUsersItemName">{{ callUser.name }}</div>
        </div>
      </div>
    </div>
    <div class="CallBar">
      <button
        v-for="control in getControlsList()"
        :key="control.name"
        class="CallBarControl"
        :class="{ '--active': controls[control.name] }"
        @click="handleCallControl(control.name)"
      >
        <Icon class="CallBarControlIcon" :name="control.icon" />
      </button>
    </div>
    <div v-if="socket" v-show="controls.chat" class="CallChatPopup">
      <Chat class="CallChat" :id="id" :user="user" :socket="socket" />
      <div class="CallChatPopupClose" @click="handleCallControl('chat')">
        <Icon class="CallChatPopupCloseIcon" name="close" />
      </div>
    </div>
  </div>
</template>
