import "./types";

declare module "./types" {
  interface CareerRun {
    player_id: string;
    seed: number;
    ranked?: boolean;
    daily_challenge_id?: string;
    attempt_no?: number;
  }
}

export {};
