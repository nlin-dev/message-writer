const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// --- Types ---

export interface PubMedResult {
  pmid: string;
  title: string;
  authors: string[];
  abstract: string;
  pub_date: string;
}

export interface SearchResponse {
  results: PubMedResult[];
}

export interface ReferenceResponse {
  id: number;
  pmid: string | null;
  title: string;
  authors: string | null;
  source: string;
  chunk_count: number;
}

export interface ReferenceListResponse {
  references: ReferenceResponse[];
}

export interface UploadResponse {
  reference_id: number;
  title: string;
  status: string;
  char_count: number;
  chunk_count: number;
}

export interface Citation {
  reference_id: number;
  chunk_id: number;
}

export type ClaimStatus = "supported" | "dropped";

export interface Claim {
  text: string;
  citations: Citation[];
  status: ClaimStatus;
  warning: string | null;
}

export interface GenerateRequest {
  prompt: string;
  reference_ids: number[];
  top_k?: number;
}

export interface GenerateResponse {
  message_id: number | null;
  message_text: string;
  claims: Claim[];
  warnings: string[];
}

export interface MessageVersionSchema {
  id: number;
  version_number: number;
  source: string;
  created_at: string;
  prompt_or_instruction: string;
  message_text: string;
  claims: Claim[];
  dropped_claims: Claim[];
}

export interface MessageSummary {
  id: number;
  status: string;
  created_at: string;
  updated_at: string;
  latest_version: MessageVersionSchema;
}

export interface MessageDetail {
  id: number;
  status: string;
  created_at: string;
  updated_at: string;
  versions: MessageVersionSchema[];
}

export interface RefineResponse {
  message_id: number;
  version_number: number;
  message_text: string;
  claims: Claim[];
  warnings: string[];
}

export interface EditResponse {
  message_id: number;
  version_number: number;
  message_text: string;
  warnings: string[];
}

export interface StatusResponse {
  id: number;
  status: "draft" | "finalized";
}

export interface SSEEvent {
  event: string;
  data: unknown;
}

// --- Helpers ---

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// --- API Functions ---

export async function searchPubMed(query: string): Promise<SearchResponse> {
  return request(`/search?query=${encodeURIComponent(query)}`);
}

export async function addFromPubMed(pmid: string): Promise<ReferenceResponse> {
  return request("/references/from-pubmed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pmid }),
  });
}

export async function getReferences(): Promise<ReferenceListResponse> {
  return request("/references");
}

export async function deleteReference(id: number): Promise<void> {
  await request(`/references/${id}`, { method: "DELETE" });
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return request("/references/upload", { method: "POST", body: form });
}

export async function* streamGenerate(body: GenerateRequest): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${BASE_URL}/messages/generate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok || !res.body) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    buffer = buffer.replace(/\r\n/g, "\n");
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.trim().split("\n");
      let event = "message";
      let data = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data = line.slice(6);
      }

      if (data) {
        yield { event, data: JSON.parse(data) };
      }
    }
  }
}

export async function getMessages(): Promise<MessageSummary[]> {
  return request("/messages");
}

export async function getMessage(id: number): Promise<MessageDetail> {
  return request(`/messages/${id}`);
}

export async function refineMessage(
  id: number,
  instruction: string,
  referenceIds: number[] = [],
  topK: number = 5,
): Promise<RefineResponse> {
  return request(`/messages/${id}/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instruction, reference_ids: referenceIds, top_k: topK }),
  });
}

export async function editMessage(id: number, text: string): Promise<EditResponse> {
  return request(`/messages/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message_text: text }),
  });
}

export async function updateMessageStatus(id: number, status: string): Promise<StatusResponse> {
  return request(`/messages/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}
