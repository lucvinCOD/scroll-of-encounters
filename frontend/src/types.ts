export type Community = { id: number; city: string; state_code: string; subdivision: string | null; description: string | null };
export type Player = { id: number; display_name: string; community_id: number; is_guest: boolean };
export type Format = { id: number; game_id: number; name: string; min_players: number; max_players: number | null; match_type: string };
export type Catalog = { communities: Community[]; players: Player[]; formats: Format[]; games: { id: number; name: string }[]; verified_matches: number };
export type User = { id: string; username: string; player_id: number | null; needs_profile?: boolean };
export type Participant = { player_id: number; display_name: string; result: "WIN" | "LOSS" | "DRAW"; is_guest: boolean };
export type Match = { id: number; community_id: number; format_id: number; format_name: string; match_date: string; approximate_start_time: string | null; status: "PENDING" | "VERIFIED" | "DISPUTED" | "CANCELLED"; author: string | null; participants: Participant[] };
export type History = { items: Match[]; total: number };
export type Registration = { id: number; status: "PENDING"; warnings: { code: string; message: string; match_ids?: number[] }[] };
export function communityName(community: Community) { return community.subdivision || community.city; }
