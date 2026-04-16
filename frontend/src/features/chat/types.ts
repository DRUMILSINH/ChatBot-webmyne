export type ChatSession = {
  id: string;
  title: string;
  vector_id: string;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
};

export type MessageRole = "user" | "assistant" | "system";

export type MessageSource = {
  rank?: number;
  score?: number;
  retrieval_source?: string;
  url?: string;
  chunk_id?: string;
  md5?: string;
  content?: string;
};

export type ChatMessage = {
  id: number;
  role: MessageRole;
  content: string;
  sources: MessageSource[];
  confidence?: number;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model_info?: {
    model: string;
  };
  latency_ms?: number;
  created_at: string;
  trace_id?: string;
};

export type DebugPayload = {
  retrieved_chunks?: MessageSource[];
  retrieved_documents?: MessageSource[];
  sources?: MessageSource[];
  source_links?: string[];
  confidence?: number;
  confidence_breakdown?: Record<string, number | string>;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model_info?: Record<string, unknown>;
  latency_ms?: Record<string, number>;
  trace_id?: string;
};

export type KnowledgeBaseSourceStat = {
  url: string;
  chunk_count: number;
};

export type KnowledgeBaseStats = {
  vector_id: string;
  total_vectors: number;
  total_chunks: number;
  metadata_records: number;
  unique_chunk_ids: number;
  unique_urls: number;
  chunks_with_source_url: number;
  chunks_without_source_url: number;
  top_sources: KnowledgeBaseSourceStat[];
  sample_urls: string[];
  generated_at: string;
};
