export interface GenerationInput {
  prompt: string;
  ratio: '9:16' | '16:9' | '1:1';
  duration: number;
  quality: 'fast' | 'standard' | 'pro';
  resolution: '480p' | '720p' | '1080p';
  generateAudio: boolean;
  quantity: 1;
}
export interface VideoProvider {
  id: string;
  name: string;
  baseUrl: string;
  configured: boolean;
  keyHint: string;
  note: string;
  capabilities: {
    ratios: GenerationInput['ratio'][];
    durations: number[];
    resolutions: GenerationInput['resolution'][];
    supportsAudio: boolean;
    requiresAudio?: boolean;
    supportsCancel?: boolean;
    maxPromptLength: number;
  };
}
export interface VideoProviders {
  activeProvider: string;
  providers: VideoProvider[];
}
export interface CostEstimate {
  credits: number;
  currency: string;
  estimatedSeconds: number;
  priceVersion: string;
}
export interface VideoTask {
  id: string;
  status:
    | 'queued'
    | 'generating'
    | 'post_processing'
    | 'succeeded'
    | 'failed'
    | 'cancelled';
  progress: number;
  stage: string;
  createdAt: number;
  completedAt: number | null;
  cancelledAt: number | null;
  resultUrl: string | null;
  errorCode: string | null;
  errorMessage: string | null;
  actionUrl: string | null;
  input: GenerationInput;
}
export interface Plan {
  id: string;
  name: string;
  monthlyCredits: number;
  price: number;
}
export interface Usage {
  plan: Plan;
  monthlyLimit: number;
  usedCredits: number;
  reservedCredits: number;
  availableCredits: number;
  renewsAt: number;
}
export interface BillingRecord {
  taskId: string | null;
  title: string;
  credits: number;
  status: string;
  createdAt: number;
}
export interface BillingEvent {
  kind: string;
  description: string;
  createdAt: number;
}
export interface Billing extends Usage {
  plans: Plan[];
  records: BillingRecord[];
  events: BillingEvent[];
}
export interface Work {
  id: string;
  title: string;
  prompt: string;
  ratio: string;
  duration: number;
  resolution: string;
  resultUrl: string;
  createdAt: number;
}
