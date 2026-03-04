export interface PlayerStats {
  player_id: number;
  team: number | null;
  total_shots: number;
  dinks: number;
  drives: number;
  drops: number;
  lobs: number;
  volleys: number;
  overheads: number;
  serves: number;
  returns: number;
  ernes: number;
  atps: number;
  resets: number;
  speedups: number;
  passing_shots: number;
  poaches: number;
  dink_accuracy: number;
  third_shot_drop_attempts: number;
  third_shot_drop_success: number;
  serve_in_pct: number;
  unforced_errors: number;
  forced_errors: number;
  winners: number;
  kitchen_time_pct: number;
  transition_time_pct: number;
  baseline_time_pct: number;
  avg_position: [number, number];
  avg_shot_speed: number;
  avg_rally_length: number;
}

export interface TeamStats {
  team_id: number;
  players: PlayerStats[];
  points_won: number;
  points_lost: number;
  side_out_pct: number;
  scoring_runs: number[];
}

export interface RallySummary {
  number: number;
  length: number;
  winner_team: number | null;
  ending: string | null;
  shots: string[];
}

export interface MatchStats {
  duration_seconds: number;
  total_points: number;
  total_rallies: number;
  avg_rally_length: number;
  longest_rally: number;
  teams: TeamStats[];
  players: PlayerStats[];
  rallies: RallySummary[];
  shot_distribution: Record<string, number>;
  score_progression: { point: number; team_0: number; team_1: number }[];
  llm_observations: string[];
}

export interface ShotEvent {
  frame_idx: number;
  timestamp: number; // seconds
  shot_type: string;
  player_id: number;
  team: number | null;
  outcome: string;
}

export type TimelineMarker = {
  time: number; // seconds
  type: "shot" | "rally_start" | "rally_end" | "point";
  label: string;
  color: string;
  rallyIndex?: number;
  shotType?: string;
};
