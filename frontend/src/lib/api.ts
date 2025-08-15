import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Check if we're in the browser environment
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Check if we're in the browser environment
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth API functions
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },
  
  register: async (email: string, password: string) => {
    const response = await api.post('/api/auth/register', { email, password });
    return response.data;
  },
  
  logout: async () => {
    const response = await api.post('/api/auth/logout');
    return response.data;
  },
};

// Chat API functions
export const chatAPI = {
  getChats: async () => {
    const response = await api.get('/api/chats');
    return response.data;
  },
  
  createChat: async (title: string) => {
    const response = await api.post('/api/chats', { title });
    return response.data;
  },
  
  getChat: async (chatId: string) => {
    const response = await api.get(`/api/chats/${chatId}`);
    return response.data;
  },
  
  sendMessage: async (chatId: string, content: string) => {
    const response = await api.post(`/api/chats/${chatId}/messages`, { content });
    return response.data;
  },
  
  deleteChat: async (chatId: string) => {
    const response = await api.delete(`/api/chats/${chatId}`);
    return response.data;
  },
};

// Document API functions
export const documentAPI = {
  uploadDocument: async (file: File, chatId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (chatId) {
      formData.append('chat_id', chatId);
    }
    
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getDocument: async (documentId: string) => {
    const response = await api.get(`/api/documents/${documentId}`);
    return response.data;
  },
  
  deleteDocument: async (documentId: string) => {
    const response = await api.delete(`/api/documents/${documentId}`);
    return response.data;
  },
};

// User API functions
export const userAPI = {
  getConfig: async () => {
    const response = await api.get('/api/user/config');
    return response.data;
  },
  
  updateConfig: async (config: any) => {
    const response = await api.post('/api/user/config', config);
    return response.data;
  },
  
  getProfile: async () => {
    const response = await api.get('/api/user/profile');
    return response.data;
  },
};