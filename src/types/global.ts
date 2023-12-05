export type DynamicObject = {
  [key: string]: any
}

export type WsConnectionEvent = {
  id: string
  event: string
  handler: (data?: any) => void
}

export type TAppSocket = {
  socket: WebSocket
  events: WsConnectionEvent[]
  on: (event: string, handler: (data?: any) => void) => TAppSocket
  off: (id: string | string[]) => TAppSocket
  send: (event: string, data?: any) => TAppSocket
  sendTo: (id: string | string[], event: string, data?: any) => TAppSocket
  [ket: string]: any
}

export type TMessage = {
  id: string
  call_id: string
  user_id: string
  user_name: string
  text: string
  created_at: number
}

export type TUser = {
  id: string
  name: string
}
