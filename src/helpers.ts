import type { DynamicObject, TAppSocket } from '@/types/global'

export function makeRequest(url: string, config: DynamicObject = {}) {
  const token = localStorage.getItem('token')
  let apiHost = import.meta.env.VITE_API_HOST
  if (apiHost[0] === '/' || !apiHost) {
    apiHost = window.location.origin + apiHost
  }
  config.headers = {
    'Content-Type': 'application/json'
  }

  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }

  if (config.body) {
    config.body = JSON.stringify(config.body)
  }

  return fetch(`${apiHost}${url}`, config).then((response) => {
    if (response.ok) {
      return response.json()
    } else {
      throw new Error(response.statusText)
    }
  })
}

export function initSocket(): Promise<TAppSocket> {
  return new Promise((resolve, reject) => {
    if (!('WebSocket' in window)) {
      return false
    }

    const token = localStorage.getItem('token')
    let apiHost = import.meta.env.VITE_API_HOST
    if (apiHost[0] === '/' || !apiHost) {
      apiHost = window.location.origin + apiHost
    }
    const socket = new WebSocket(`${apiHost.replace('http', 'ws')}/echo?token=${token}`)
    const appSocket = initAppSocket(socket)

    socket.onopen = () => {
      resolve(appSocket)
    }
    socket.onerror = () => {
      reject()
      // setTimeout(() => initSocket(token), 1000)
    }
    socket.onclose = () => {
      reject()
    }
  })
}

function initAppSocket(socket: WebSocket) {
  const appSocket: TAppSocket = {
    socket,
    events: [],
    on: (event: string, handler: (data?: any) => void) => {
      const obj = appSocket.events.find(
        (item) => item.event === event && String(item.handler) === String(handler)
      )

      if (!obj) {
        const id = Date.now() + '-' + Math.random().toString().substring(2, 7)
        appSocket.events.push({ id, event, handler })
      }

      return appSocket
    },
    off: (id: string | string[]) => {
      id = id instanceof Array ? id : [id]
      appSocket.events = appSocket.events.filter((item) => !id.includes(item.id))
      return appSocket
    },
    send: (event: string, data?: any) => {
      socket.send(JSON.stringify([event, data]))
      return appSocket
    },
    sendTo: (id: string | string[], event: string, data?: any) => {
      const ids = id instanceof Array ? id : [id]

      Object.keys(appSocket.sockets).forEach((id) => {
        if (ids.includes(id)) {
          appSocket.sockets[id].send(JSON.stringify([event, data]))
        }
      })

      return appSocket
    }
  }

  socket.onmessage = (message) => {
    const args = JSON.parse(message.data)
    const event = args[0]
    if (appSocket.events) {
      appSocket.events.forEach((item) => {
        if (item.event === event) {
          item.handler(args[1])
        }
      })
    }
  }

  return appSocket
}

export function formatDate(value: string | number | Date, format: string) {
  if (!(value instanceof Date)) {
    value = new Date(value)
  }

  const months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
  ]

  return format
    .replace('YYYY', value.getFullYear().toString())
    .replace('MMM', months[value.getMonth()])
    .replace('MM', ('0' + (value.getMonth() + 1)).slice(-2))
    .replace('DD', ('0' + value.getDate()).slice(-2))
    .replace('HH', ('0' + value.getHours()).slice(-2))
    .replace('mm', ('0' + value.getMinutes()).slice(-2))
    .replace('ss', ('0' + value.getSeconds()).slice(-2))
    .replace('sss', ('0' + value.getMilliseconds()).slice(-3))
}

export function stringToColor(str: string) {
  let hash = 0
  str.split('').forEach((char) => {
    hash = char.charCodeAt(0) + ((hash << 5) - hash)
  })
  let colour = '#'
  for (let i = 0; i < 3; i++) {
    const value = (hash >> (i * 8)) & 0xff
    colour += value.toString(16).padStart(2, '0')
  }
  return colour
}

export function copyToClipboard(element: HTMLElement): Promise<string> {
  return new Promise((resolve, reject) => {
    const range = document.createRange()
    range.selectNode(element)

    const selection = window.getSelection()
    selection?.removeAllRanges()
    selection?.addRange(range)

    try {
      const ok = document.execCommand('copy')

      if (ok) {
        resolve('Copied to clipboard')
      } else {
        reject('Unable to copy')
      }
    } catch (err) {
      reject('Unsupported browser')
    }

    selection?.removeAllRanges()
  })
}
