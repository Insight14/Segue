/**
 * Auto-generated OpenAPI TypeScript definitions for Convo Glasses Mobile Client.
 * Do not edit manually. Generated from OpenAPI schema.
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
