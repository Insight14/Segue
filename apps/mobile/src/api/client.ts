import type {
  DocumentProcessResponse,
  DocumentResponse,
  DocumentUploadRequest,
  DocumentUploadResponse,
  FactCreate,
  FactResponse,
  FactUpdate,
  ListFactsParams,
  ProfileResponse,
  ProfileUpdate,
} from "./types";

export interface ApiClientConfig {
  baseUrl: string;
  getAuthToken?: () => Promise<string | null> | string | null;
}

export class ConvoGlassesClient {
  private baseUrl: string;
  private getAuthToken?: () => Promise<string | null> | string | null;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, "");
    this.getAuthToken = config.getAuthToken;
  }

  private async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.getAuthToken) {
      const token = await this.getAuthToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`API Error ${response.status}: ${errorBody}`);
    }

    if (response.status === 204) {
      return undefined as unknown as T;
    }

    return response.json() as Promise<T>;
  }

  // Health Probes
  async healthz(): Promise<{ status: string }> {
    return this.fetch<{ status: string }>("/healthz");
  }

  async readyz(): Promise<{ status: string; dependencies?: Record<string, string> }> {
    return this.fetch<{ status: string; dependencies?: Record<string, string> }>("/readyz");
  }

  // Profile
  async getProfile(): Promise<ProfileResponse> {
    return this.fetch<ProfileResponse>("/v1/profile");
  }

  async updateProfile(data: ProfileUpdate): Promise<ProfileResponse> {
    return this.fetch<ProfileResponse>("/v1/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  // Facts
  async listFacts(params?: ListFactsParams): Promise<FactResponse[]> {
    const query = new URLSearchParams();
    if (params?.kind) query.set("kind", params.kind);
    if (params?.confirmed !== undefined) query.set("confirmed", String(params.confirmed));
    if (params?.tag) query.set("tag", params.tag);

    const qs = query.toString();
    const endpoint = `/v1/facts${qs ? `?${qs}` : ""}`;
    return this.fetch<FactResponse[]>(endpoint);
  }

  async getReviewFacts(): Promise<FactResponse[]> {
    return this.fetch<FactResponse[]>("/v1/facts/review");
  }

  async createFact(data: FactCreate): Promise<FactResponse> {
    return this.fetch<FactResponse>("/v1/facts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async confirmFact(id: string): Promise<FactResponse> {
    return this.fetch<FactResponse>(`/v1/facts/${id}/confirm`, {
      method: "POST",
    });
  }

  async updateFact(id: string, data: FactUpdate): Promise<FactResponse> {
    return this.fetch<FactResponse>(`/v1/facts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteFact(id: string): Promise<void> {
    return this.fetch<void>(`/v1/facts/${id}`, {
      method: "DELETE",
    });
  }

  // Documents
  async createDocumentUploadUrl(data: DocumentUploadRequest): Promise<DocumentUploadResponse> {
    return this.fetch<DocumentUploadResponse>("/v1/documents/upload-url", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async processDocument(id: string): Promise<DocumentProcessResponse> {
    return this.fetch<DocumentProcessResponse>(`/v1/documents/${id}/process`, {
      method: "POST",
    });
  }

  async getDocument(id: string): Promise<DocumentResponse> {
    return this.fetch<DocumentResponse>(`/v1/documents/${id}`);
  }

  async listDocuments(): Promise<DocumentResponse[]> {
    return this.fetch<DocumentResponse[]>("/v1/documents");
  }
}
