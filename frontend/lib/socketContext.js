import React from 'react'
import { io } from 'socket.io-client'

export const SocketContext = React.createContext(null)
export function SocketProvider({ url, children }) {
    const socketRef = React.useRef(null)
    React.useEffect(() => {
        socketRef.current = io(url)
        return () => socketRef.current?.close()
    }, [url])
    return <SocketContext.Provider value={socketRef.current}>{children}</SocketContext.Provider>
}

export function useSocket() {
    return React.useContext(SocketContext)
}