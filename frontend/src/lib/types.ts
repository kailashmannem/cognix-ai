// Type definitions for the application

export interface User {
  id: string;
  email: string;
  preferred_llm_provider: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  document_name?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  context_used?: string[];
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface UserConfig {
  api_keys?: Record<string, string>;
  user_mongodb_connection?: string;
  preferred_llm_provider?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface ChatCreateRequest {
  title: string;
}

export interface MessageCreateRequest {
  content: string;
}