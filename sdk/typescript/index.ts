export type CefrBand = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";

export type SkillName =
  | "vocabulary"
  | "grammar"
  | "reading"
  | "writing"
  | "listening"
  | "speaking"
  | string;

export interface AssessTextRequest {
  language?: string;
  text: string;
  skill?: SkillName;
}

export interface FrameworkBands {
  cefr: CefrBand;
  jlpt?: string;
  topik?: string;
  hsk?: string;
  ielts_approx?: number;
  toeic_approx?: number;
}

export interface TextFeatures {
  tokens: number;
  unique_tokens: number;
  avg_token_len: number;
  script_bonus: number;
  connectors: number;
  sentences: number;
}

export interface AssessTextResponse {
  language: string;
  language_name: string;
  frameworks: string[];
  skill: string;
  score: number;
  cefr: CefrBand;
  framework_bands: FrameworkBands;
  features: TextFeatures;
  model: string;
  integration_version?: string;
  ready_for_ui?: boolean;
}

export interface DemoResponse {
  language: string;
  language_name: string;
  frameworks: string[];
  skills: Record<string, number>;
  overall: number;
  cefr: CefrBand;
  framework_bands: FrameworkBands;
  demo_text: string;
  model: string;
  integration_version?: string;
}

export type AssessResponse = AssessTextResponse | DemoResponse;
