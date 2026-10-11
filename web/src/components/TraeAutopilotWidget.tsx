import { useEffect, useState, useCallback } from "react";
import {
  fetchTraeStatus,
  toggleTraeAutopilot,
  triggerTraeUnblock,
  sendTraeMessage,
  triggerTraeNewTask,
  triggerTraeSmartUnblock,
  type TraeAutopilotStatus,
  type TraeProjectStatus,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Zap, Bot, Send, RefreshCw, CheckCircle2, Plus, BrainCircuit, FolderOpen, Activity } from "lucide-react";

interface TraeAutopilotWidgetProps {
  compact?: boolean;
  className?: string;
}

export function TraeAutopilotWidget({ compact = false, className }: TraeAutopilotWidgetProps) {
  const [status, setStatus] = useState<TraeAutopilotStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetchTraeStatus();
      setStatus(res);
      // Auto-select first project if none selected
      if (!selectedProject && res.projects) {
        const projectNames = Object.keys(res.projects);
        if (projectNames.length > 0) {
          setSelectedProject(projectNames[0]);
        }
      }
    } catch {
      // Ignore network errors during polling
    }
  }, [selectedProject]);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 4000);
    return () => clearInterval(interval);
  }, [loadStatus]);

  const showFeedback = (msg: string, duration = 3000) => {
    setFeedback(msg);
    setTimeout(() => setFeedback(null), duration);
  };

  const handleToggle = async () => {
    if (!status) return;
    setLoading(true);
    try {
      const res = await toggleTraeAutopilot(!status.enabled);
      setStatus((prev) => (prev ? { ...prev, enabled: res.enabled, status: res.status } : null));
      showFeedback(res.enabled ? "Autopilot: ON" : "Autopilot: OFF", 2500);
    } catch (err: any) {
      showFeedback(`Error: ${err.message || "Failed"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUnblock = async () => {
    if (!selectedProject) return showFeedback("Select a project first");
    setActionLoading("unblock");
    try {
      const res = await triggerTraeUnblock(selectedProject ?? undefined);
      if (res.ok) {
        showFeedback(`Unblock [${selectedProject || "all"}] ✓`);
        loadStatus();
      } else {
        showFeedback(`Unblock error: ${res.error || "failed"}`);
      }
    } catch (err: any) {
      showFeedback(`Error: ${err.message || "Failed"}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSmartUnblock = async () => {
    if (!selectedProject) return showFeedback("Select a project first");
    setActionLoading("smart");
    try {
      const res = await triggerTraeSmartUnblock(selectedProject ?? undefined);
      if (res.ok) {
        const promptPreview = res.smart_prompt
          ? res.smart_prompt.substring(0, 60) + (res.smart_prompt.length > 60 ? "…" : "")
          : "sent";
        showFeedback(`Smart Unblock [${res.project || selectedProject || "all"}]: ${promptPreview} ✓`);
        loadStatus();
      } else {
        showFeedback(`Smart Unblock error: ${res.error || "failed"}`);
      }
    } catch (err: any) {
      showFeedback(`Error: ${err.message || "Failed"}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleNewTask = async () => {
    if (!selectedProject) return showFeedback("Select a project first");
    setActionLoading("newtask");
    try {
      const res = await triggerTraeNewTask(selectedProject ?? undefined);
      if (res.ok) {
        showFeedback(`New Task [${selectedProject || "all"}] ✓ (Ctrl+Alt+N)`);
        loadStatus();
      } else {
        showFeedback(`New Task error: ${res.error || "failed"}`);
      }
    } catch (err: any) {
      showFeedback(`Error: ${err.message || "Failed"}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSendContinue = async () => {
    if (!selectedProject) return showFeedback("Select a project first");
    setActionLoading("send");
    try {
      const res = await sendTraeMessage("Tiếp tục tasks", selectedProject ?? undefined);
      if (res.ok) {
        showFeedback(`Sent 'Tiếp tục tasks' → [${selectedProject || "all"}] ✓`);
        loadStatus();
      } else {
        showFeedback(`Send error: ${res.error || "failed"}`);
      }
    } catch (err: any) {
      showFeedback(`Error: ${err.message || "Failed"}`);
    } finally {
      setActionLoading(null);
    }
  };

  const isEnabled = status?.enabled ?? true;
  const isCdpActive = status?.cdp_connected ?? false;
  const port = status?.port ?? 9339;
  const projects = status?.projects ?? {};
  const projectNames = Object.keys(projects);
  const selectedProjectStatus: TraeProjectStatus | null =
    selectedProject && projects[selectedProject] ? projects[selectedProject] : null;

  if (compact) {
    return (
      <div className={cn("px-5 py-2 border-t border-midground/10 text-xs font-sans", className)}>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 min-w-0">
            <span
              className={cn(
                "h-2 w-2 rounded-full shrink-0",
                !isCdpActive
                  ? "bg-destructive animate-pulse"
                  : isEnabled
                  ? "bg-emerald-500"
                  : "bg-muted-foreground"
              )}
            />
            <span className="truncate font-medium text-text-secondary">
              Trae Autopilot
              {projectNames.length > 0 && (
                <span className="text-text-tertiary ml-1">({projectNames.length} projects)</span>
              )}
            </span>
          </div>

          <button
            type="button"
            disabled={loading}
            onClick={handleToggle}
            className={cn(
              "px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase transition-colors",
              isEnabled
                ? "bg-emerald-500/15 text-emerald-500 hover:bg-emerald-500/25 border border-emerald-500/30"
                : "bg-muted text-muted-foreground hover:bg-muted/80 border border-muted-foreground/20"
            )}
          >
            {isEnabled ? "ON" : "OFF"}
          </button>
        </div>

        {feedback && (
          <p className="mt-1 text-[11px] text-emerald-500 truncate animate-fade-in">
            {feedback}
          </p>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-lg border border-midground/15 bg-background/60 backdrop-blur-sm p-3.5 shadow-sm text-xs font-sans flex flex-col gap-2.5",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "p-1.5 rounded-md",
              isEnabled && isCdpActive ? "bg-emerald-500/15 text-emerald-500" : "bg-muted text-muted-foreground"
            )}
          >
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <h4 className="font-semibold text-text-primary text-xs leading-none">Trae Autopilot</h4>
            <span className="text-[11px] text-text-tertiary">Multi-Window CDP Controller</span>
          </div>
        </div>

        {/* Toggle Switch */}
        <button
          type="button"
          disabled={loading}
          onClick={handleToggle}
          aria-label="Toggle Autopilot"
          className={cn(
            "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500",
            isEnabled ? "bg-emerald-500" : "bg-muted"
          )}
        >
          <span
            className={cn(
              "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out",
              isEnabled ? "translate-x-4" : "translate-x-0"
            )}
          />
        </button>
      </div>

      {/* Project Selector */}
      {projectNames.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-1 text-[11px] text-text-tertiary">
            <FolderOpen className="h-3 w-3" />
            <span>Projects ({projectNames.length})</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {projectNames.map((name) => {
              const projStatus = projects[name];
              const isSelected = selectedProject === name;
              const isGenerating = projStatus?.is_generating ?? false;
              return (
                <button
                  key={name}
                  type="button"
                  onClick={() => setSelectedProject(name)}
                  className={cn(
                    "flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium transition-all border",
                    isSelected
                      ? "bg-emerald-500/15 text-emerald-500 border-emerald-500/30 shadow-sm"
                      : "bg-midground/5 text-text-secondary border-midground/10 hover:bg-midground/15 hover:border-midground/20"
                  )}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full shrink-0",
                      isGenerating ? "bg-amber-500 animate-pulse" : "bg-emerald-500"
                    )}
                  />
                  <span className="truncate max-w-[100px]">{name}</span>
                  {isGenerating && (
                    <Activity className="h-2.5 w-2.5 text-amber-500 animate-pulse" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Status Bar */}
      <div className="flex items-center justify-between text-[11px] bg-midground/5 px-2.5 py-1.5 rounded border border-midground/10">
        <div className="flex items-center gap-1.5 truncate">
          <span
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              !isCdpActive ? "bg-destructive animate-pulse" : isEnabled ? "bg-emerald-500" : "bg-muted-foreground"
            )}
          />
          <span className="text-text-secondary truncate">
            {isCdpActive
              ? selectedProjectStatus
                ? `${selectedProject}${selectedProjectStatus.active_file ? ` · ${selectedProjectStatus.active_file}` : ""}`
                : `Port ${port} Active · ${projectNames.length} project${projectNames.length !== 1 ? "s" : ""}`
              : "CDP Disconnected"}
          </span>
        </div>

        <span className="text-[10px] text-text-tertiary uppercase font-mono">
          {selectedProjectStatus?.is_generating ? "Generating" : isEnabled ? "Auto" : "Manual"}
        </span>
      </div>

      {/* Action Buttons — 2x2 grid */}
      <div className="grid grid-cols-2 gap-1.5 pt-0.5">
        {/* Smart Unblock — primary action */}
        <button
          type="button"
          disabled={actionLoading !== null}
          onClick={handleSmartUnblock}
          className="flex items-center justify-center gap-1.5 px-2 py-1.5 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 text-[11px] font-medium transition-colors border border-emerald-500/20"
        >
          {actionLoading === "smart" ? (
            <RefreshCw className="h-3 w-3 animate-spin" />
          ) : (
            <BrainCircuit className="h-3 w-3" />
          )}
          <span>Smart Unblock</span>
        </button>

        {/* New Task */}
        <button
          type="button"
          disabled={actionLoading !== null}
          onClick={handleNewTask}
          className="flex items-center justify-center gap-1.5 px-2 py-1.5 rounded bg-midground/10 hover:bg-midground/20 text-text-secondary hover:text-text-primary text-[11px] font-medium transition-colors border border-midground/15"
        >
          {actionLoading === "newtask" ? (
            <RefreshCw className="h-3 w-3 animate-spin" />
          ) : (
            <Plus className="h-3 w-3 text-blue-500" />
          )}
          <span>New Task</span>
        </button>

        {/* Unblock Now (legacy) */}
        <button
          type="button"
          disabled={actionLoading !== null}
          onClick={handleUnblock}
          className="flex items-center justify-center gap-1.5 px-2 py-1.5 rounded bg-midground/10 hover:bg-midground/20 text-text-secondary hover:text-text-primary text-[11px] font-medium transition-colors border border-midground/15"
        >
          {actionLoading === "unblock" ? (
            <RefreshCw className="h-3 w-3 animate-spin" />
          ) : (
            <Zap className="h-3 w-3 text-amber-500" />
          )}
          <span>Unblock</span>
        </button>

        {/* Continue */}
        <button
          type="button"
          disabled={actionLoading !== null}
          onClick={handleSendContinue}
          className="flex items-center justify-center gap-1.5 px-2 py-1.5 rounded bg-midground/10 hover:bg-midground/20 text-text-secondary hover:text-text-primary text-[11px] font-medium transition-colors border border-midground/15"
        >
          {actionLoading === "send" ? (
            <RefreshCw className="h-3 w-3 animate-spin" />
          ) : (
            <Send className="h-3 w-3 text-emerald-500" />
          )}
          <span>Continue</span>
        </button>
      </div>

      {feedback && (
        <div className="flex items-center gap-1 text-[11px] text-emerald-500 truncate animate-fade-in">
          <CheckCircle2 className="h-3 w-3 shrink-0" />
          <span className="truncate">{feedback}</span>
        </div>
      )}
    </div>
  );
}
