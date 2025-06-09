
let socket = null;

const WEBSOCKET_URL = 'ws://localhost:8000/ws';

export const connectWebSocket = (conversationId, token, onMessageCallback) => {
  // Disconnect any existing socket before creating a new one
  if (socket) {
    disconnectWebSocket();
  }

  socket = new WebSocket(`${WEBSOCKET_URL}/${conversationId}/${token}`);

  socket.onopen = () => {
    console.log(`WebSocket connected to conversation ${conversationId}`);
  };

  socket.onmessage = (event) => {
    // Defensively check if the callback is a function before calling it
    if (onMessageCallback && typeof onMessageCallback === 'function') {
      onMessageCallback(event);
    }
  };

  socket.onclose = () => {
    console.log('WebSocket disconnected');
    // Nullify the socket variable so we know we are disconnected
    socket = null; 
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
};

export const disconnectWebSocket = () => {
  if (socket) {
    // Remove listeners before closing to prevent race conditions on close
    socket.onopen = null;
    socket.onmessage = null;
    socket.onclose = null;
    socket.onerror = null;
    socket.close();
    socket = null;
  }
};

export const sendMessage = (message) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(message);
  } else {
    console.error('WebSocket is not connected or not in an open state.');
  }
};