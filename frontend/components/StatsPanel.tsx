"use client";

import { MatchStats, PlayerStats as PlayerStatsType } from "@/lib/types";

interface StatsPanelProps {
  stats: MatchStats;
  currentTime: number;
}

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-3">
      <div className="text-xs text-[var(--text-secondary)] mb-1">{label}</div>
      <div className="text-xl font-bold" style={color ? { color } : undefined}>
        {value}
      </div>
      {sub && <div className="text-xs text-[var(--text-secondary)] mt-0.5">{sub}</div>}
    </div>
  );
}

function ShotBar({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-16 text-[var(--text-secondary)] text-xs">{label}</span>
      <div className="flex-1 h-4 bg-[var(--bg)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="w-8 text-right tabular-nums text-xs">{count}</span>
    </div>
  );
}

function PositionBar({ player }: { player: PlayerStatsType }) {
  return (
    <div className="flex h-3 rounded-full overflow-hidden bg-[var(--bg)]">
      <div
        className="bg-[#22c55e]"
        style={{ width: `${player.kitchen_time_pct}%` }}
        title={`Kitchen: ${player.kitchen_time_pct.toFixed(0)}%`}
      />
      <div
        className="bg-[#f59e0b]"
        style={{ width: `${player.transition_time_pct}%` }}
        title={`Transition: ${player.transition_time_pct.toFixed(0)}%`}
      />
      <div
        className="bg-[#ef4444]"
        style={{ width: `${player.baseline_time_pct}%` }}
        title={`Baseline: ${player.baseline_time_pct.toFixed(0)}%`}
      />
    </div>
  );
}

function PlayerCard({ player }: { player: PlayerStatsType }) {
  const teamLabel = player.team === 0 ? "Near" : player.team === 1 ? "Far" : "?";
  const teamColor = player.team === 0 ? "#22c55e" : "#3b82f6";
  const totalShots = player.total_shots || 1;

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: teamColor }} />
        <span className="font-semibold">Player {player.player_id}</span>
        <span className="text-xs text-[var(--text-secondary)] bg-[var(--bg)] px-2 py-0.5 rounded">
          Team {teamLabel}
        </span>
      </div>

      {/* Shot breakdown */}
      <div className="space-y-1.5">
        <ShotBar label="Dinks" count={player.dinks} total={totalShots} color="#22c55e" />
        <ShotBar label="Drives" count={player.drives} total={totalShots} color="#ef4444" />
        <ShotBar label="Drops" count={player.drops} total={totalShots} color="#f59e0b" />
        <ShotBar label="Volleys" count={player.volleys} total={totalShots} color="#ec4899" />
        <ShotBar label="Lobs" count={player.lobs} total={totalShots} color="#06b6d4" />
        <ShotBar label="Serves" count={player.serves} total={totalShots} color="#3b82f6" />
        <ShotBar label="Ernes" count={player.ernes} total={totalShots} color="#a855f7" />
        <ShotBar label="ATPs" count={player.atps} total={totalShots} color="#14b8a6" />
        <ShotBar label="Resets" count={player.resets} total={totalShots} color="#64748b" />
        <ShotBar label="Speedups" count={player.speedups} total={totalShots} color="#dc2626" />
        <ShotBar label="Passing" count={player.passing_shots} total={totalShots} color="#0ea5e9" />
        <ShotBar label="Poaches" count={player.poaches} total={totalShots} color="#d946ef" />
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-[var(--bg)] rounded-lg p-2">
          <div className="text-lg font-bold">{player.dink_accuracy.toFixed(0)}%</div>
          <div className="text-[10px] text-[var(--text-secondary)]">Dink Acc.</div>
        </div>
        <div className="bg-[var(--bg)] rounded-lg p-2">
          <div className="text-lg font-bold">{player.unforced_errors}</div>
          <div className="text-[10px] text-[var(--text-secondary)]">UE</div>
        </div>
        <div className="bg-[var(--bg)] rounded-lg p-2">
          <div className="text-lg font-bold">{player.winners}</div>
          <div className="text-[10px] text-[var(--text-secondary)]">Winners</div>
        </div>
      </div>

      {/* 3rd shot drop */}
      {player.third_shot_drop_attempts > 0 && (
        <div className="text-xs text-[var(--text-secondary)]">
          3rd Shot Drop: {player.third_shot_drop_attempts} attempts,{" "}
          {player.third_shot_drop_success.toFixed(0)}% success
        </div>
      )}

      {/* Position breakdown */}
      <div>
        <div className="text-xs text-[var(--text-secondary)] mb-1">Court Position</div>
        <PositionBar player={player} />
        <div className="flex justify-between text-[10px] text-[var(--text-secondary)] mt-1">
          <span>🟢 Kitchen {player.kitchen_time_pct.toFixed(0)}%</span>
          <span>🟡 Trans. {player.transition_time_pct.toFixed(0)}%</span>
          <span>🔴 Base. {player.baseline_time_pct.toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}

export default function StatsPanel({ stats, currentTime }: StatsPanelProps) {
  // Find current rally based on time
  const currentRallyIdx = stats.rallies.findIndex((r, i) => {
    const nextRally = stats.rallies[i + 1];
    if (!nextRally) return true;
    // Rough estimate — we don't have exact timestamps per rally yet
    return true;
  });

  return (
    <div className="space-y-4 overflow-y-auto max-h-[calc(100vh-2rem)]">
      {/* Match Overview */}
      <div>
        <h2 className="text-lg font-bold mb-3">Match Overview</h2>
        <div className="grid grid-cols-2 gap-2">
          <StatCard
            label="Duration"
            value={`${Math.floor(stats.duration_seconds / 60)}:${Math.floor(stats.duration_seconds % 60).toString().padStart(2, "0")}`}
          />
          <StatCard label="Total Rallies" value={stats.total_rallies} />
          <StatCard
            label="Avg Rally Length"
            value={`${stats.avg_rally_length.toFixed(1)}`}
            sub="shots"
          />
          <StatCard label="Longest Rally" value={stats.longest_rally} sub="shots" />
        </div>
      </div>

      {/* Team Score */}
      {stats.teams.length === 2 && (
        <div>
          <h2 className="text-lg font-bold mb-3">Score</h2>
          <div className="flex items-center justify-center gap-6 bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-[#22c55e]">
                {stats.teams[0].points_won}
              </div>
              <div className="text-xs text-[var(--text-secondary)]">Team Near</div>
            </div>
            <div className="text-2xl text-[var(--text-secondary)]">—</div>
            <div className="text-center">
              <div className="text-3xl font-bold text-[#3b82f6]">
                {stats.teams[1].points_won}
              </div>
              <div className="text-xs text-[var(--text-secondary)]">Team Far</div>
            </div>
          </div>
        </div>
      )}

      {/* Shot Distribution */}
      <div>
        <h2 className="text-lg font-bold mb-3">Shot Distribution</h2>
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-4 space-y-2">
          {Object.entries(stats.shot_distribution)
            .sort(([, a], [, b]) => b - a)
            .map(([type, count]) => {
              const colors: Record<string, string> = {
                serve: "#3b82f6",
                return: "#8b5cf6",
                dink: "#22c55e",
                drive: "#ef4444",
                drop: "#f59e0b",
                lob: "#06b6d4",
                volley: "#ec4899",
                overhead: "#f97316",
                erne: "#a855f7",
                atp: "#14b8a6",
                reset: "#64748b",
                speedup: "#dc2626",
                passing: "#0ea5e9",
                poach: "#d946ef",
              };
              const total = Object.values(stats.shot_distribution).reduce((a, b) => a + b, 0);
              return (
                <ShotBar
                  key={type}
                  label={type.charAt(0).toUpperCase() + type.slice(1)}
                  count={count}
                  total={total}
                  color={colors[type] || "#888"}
                />
              );
            })}
        </div>
      </div>

      {/* Player Cards */}
      <div>
        <h2 className="text-lg font-bold mb-3">Players</h2>
        <div className="space-y-3">
          {stats.players.map((player) => (
            <PlayerCard key={player.player_id} player={player} />
          ))}
        </div>
      </div>

      {/* AI Observations */}
      {stats.llm_observations && stats.llm_observations.length > 0 && (
        <div>
          <h2 className="text-lg font-bold mb-3">🧠 AI Observations</h2>
          <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-4 space-y-2">
            {stats.llm_observations.map((obs, i) => (
              <div key={i} className="flex gap-2 text-sm">
                <span className="text-[var(--accent)]">•</span>
                <span>{obs}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rally Log */}
      <div>
        <h2 className="text-lg font-bold mb-3">Rally Log</h2>
        <div className="space-y-1.5 max-h-64 overflow-y-auto">
          {stats.rallies.map((rally, i) => (
            <div
              key={i}
              className="flex items-center gap-2 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs"
            >
              <span className="text-[var(--text-secondary)] w-6">#{rally.number}</span>
              <div className="flex gap-0.5 flex-1 flex-wrap">
                {rally.shots.map((shot, j) => {
                  const colors: Record<string, string> = {
                    serve: "#3b82f6",
                    return: "#8b5cf6",
                    dink: "#22c55e",
                    drive: "#ef4444",
                    drop: "#f59e0b",
                    lob: "#06b6d4",
                    volley: "#ec4899",
                    overhead: "#f97316",
                  };
                  return (
                    <span
                      key={j}
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: colors[shot] || "#666" }}
                      title={shot}
                    />
                  );
                })}
              </div>
              <span className="text-[var(--text-secondary)]">{rally.length} shots</span>
              {rally.winner_team !== null && (
                <span
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: rally.winner_team === 0 ? "#22c55e" : "#3b82f6",
                  }}
                  title={`Won by Team ${rally.winner_team === 0 ? "Near" : "Far"}`}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
