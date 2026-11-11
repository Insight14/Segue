/**
 * Auto-generated OpenAPI TypeScript definitions for Convo Glasses Mobile Client.
 * Generated from OpenAPI schema.
 */

export type FactKind =
  | "experience"
  | "education"
  | "skill"
  | "interest"
  | "hobby"
  | "goal"
  | "value"
  | "story_success"
  | "story_failure"
  | "story_collaboration"
  | "other";

export type FactSource = "user" | "resume" | "agent";

export type ThreadMode = "discover" | "prep";

export interface ProfileResponse {
  headline?: string | null;
  status?: string | null;
  goals?: string | null;
  tone_preference?: string | null;
  summary_md?: string | null;
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProfileUpdate {
  headline?: string | null;
  status?: string | null;
  goals?: string | null;
  tone_preference?: string | null;
  summary_md?: string | null;
}

export interface FactResponse {
  id: string;
  user_id: string;
  kind: FactKind;
  title: string;
  body: string;
  tags: string[];
  source: FactSource;
  confirmed: boolean;
  created_at: string;
  updated_at: string;
}

export interface FactCreate {
  kind: FactKind;
  title: string;
  body: string;
  tags?: string[];
  source?: FactSource;
  confirmed?: boolean;
}

export interface FactUpdate {
  kind?: FactKind | null;
  title?: string | null;
  body?: string | null;
  tags?: string[] | null;
  confirmed?: boolean | null;
}

export interface ListFactsParams {
  kind?: FactKind;
  confirmed?: boolean;
  tag?: string;
}

export interface DocumentUploadRequest {
  filename: string;
  mime?: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  upload_url: string;
  s3_key: string;
}

export interface DocumentProcessResponse {
  document_id: string;
  status: string;
  message: string;
}

export interface DocumentResponse {
  id: string;
  user_id: string;
  filename: string;
  mime: string;
  status: string;
  parsed_text?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ThreadCreateRequest {
  mode: ThreadMode;
  title?: string;
}

export interface MessageResponse {
  id: string;
  thread_id: string;
  role: string;
  content: string;
  proposed_fact?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ThreadResponse {
  id: string;
  user_id: string;
  mode: ThreadMode;
  title: string;
  messages: MessageResponse[];
  created_at: string;
  updated_at: string;
}

export interface TalkingPointStory {
  title: string;
  situation: string;
  action: string;
  result: string;
  fact_id?: string | null;
}

export interface TalkingPointsContent {
  pitch_30s: string;
  stories: TalkingPointStory[];
  questions_to_ask: string[];
  icebreakers: string[];
  if_asked_about_weakness?: string | null;
  gaps: string[];
}

export interface GenerateTalkingPointsRequest {
  event_id?: string | null;
  contact_id?: string | null;
  notes?: string | null;
}

export interface TalkingPointsResponse {
  id: string;
  user_id: string;
  event_id?: string | null;
  contact_id?: string | null;
  content: TalkingPointsContent;
  created_at: string;
  updated_at: string;
}

// Milestone M5 Types

export interface EventBase {
  name: string;
  date?: string | null;
  type?: string | null;
  notes?: string | null;
}

export interface EventCreate extends EventBase {}
export interface EventUpdate extends Partial<EventBase> {}

export interface EventResponse extends EventBase {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ContactBase {
  event_id?: string | null;
  name: string;
  company?: string | null;
  role?: string | null;
  notes?: string | null;
  consent_noted?: boolean;
}

export interface ContactCreate extends ContactBase {}
export interface ContactUpdate extends Partial<ContactBase> {}

export interface ContactResponse extends ContactBase {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessageCreate {
  speaker: "user" | "partner";
  text: string;
  seq?: number;
}

export interface ConversationMessageResponse {
  id: string;
  conversation_id: string;
  seq: number;
  speaker: string;
  text: string;
  created_at: string;
}

export interface SuggestionResponse {
  id: string;
  conversation_id: string;
  after_message_seq: number;
  type: string;
  text: string;
  shown: boolean;
  selected: boolean;
  rating?: number | null;
  created_at: string;
}

export interface SuggestionUpdate {
  shown?: boolean;
  selected?: boolean;
  rating?: number | null;
}

export interface ConversationCreate {
  contact_id?: string | null;
  event_id?: string | null;
  source?: "phone" | "laptop" | "glasses";
}

export interface ConversationUpdate {
  ended_at?: string | null;
  summary?: string | null;
}

export interface ConversationResponse {
  id: string;
  user_id: string;
  contact_id?: string | null;
  event_id?: string | null;
  started_at: string;
  ended_at?: string | null;
  summary?: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetailResponse extends ConversationResponse {
  contact?: ContactResponse | null;
  event?: EventResponse | null;
  messages: ConversationMessageResponse[];
  suggestions: SuggestionResponse[];
}
