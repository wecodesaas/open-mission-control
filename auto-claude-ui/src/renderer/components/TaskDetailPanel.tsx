import { useState, useRef, useEffect } from 'react';
import {
  X,
  Play,
  Square,
  CheckCircle2,
  XCircle,
  AlertCircle,
  AlertTriangle,
  Clock,
  FileCode,
  Terminal,
  Target,
  Bug,
  Wrench,
  Shield,
  Gauge,
  Palette,
  Lightbulb,
  Users,
  GitBranch,
  ListChecks,
  Loader2,
  RotateCcw,
  Pencil,
  Save,
  Image as ImageIcon
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { cn, calculateProgress, formatRelativeTime } from '../lib/utils';
import {
  TASK_STATUS_LABELS,
  TASK_CATEGORY_LABELS,
  TASK_CATEGORY_COLORS,
  TASK_COMPLEXITY_LABELS,
  TASK_COMPLEXITY_COLORS,
  TASK_IMPACT_LABELS,
  TASK_IMPACT_COLORS,
  TASK_PRIORITY_LABELS,
  TASK_PRIORITY_COLORS,
  IDEATION_TYPE_LABELS,
  EXECUTION_PHASE_LABELS,
  EXECUTION_PHASE_BADGE_COLORS,
  EXECUTION_PHASE_COLORS
} from '../../shared/constants';
import { startTask, stopTask, submitReview, checkTaskRunning, recoverStuckTask, persistUpdateTask } from '../stores/task-store';
import type { Task, TaskCategory, ExecutionPhase } from '../../shared/types';

// Category icon mapping
const CategoryIcon: Record<TaskCategory, typeof Target> = {
  feature: Target,
  bug_fix: Bug,
  refactoring: Wrench,
  documentation: FileCode,
  security: Shield,
  performance: Gauge,
  ui_ux: Palette,
  infrastructure: Wrench,
  testing: FileCode
};

interface TaskDetailPanelProps {
  task: Task;
  onClose: () => void;
}

export function TaskDetailPanel({ task, onClose }: TaskDetailPanelProps) {
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false);
  const [isStuck, setIsStuck] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [hasCheckedRunning, setHasCheckedRunning] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);
  const [editDescription, setEditDescription] = useState(task.description);
  const [isSaving, setIsSaving] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  const progress = calculateProgress(task.chunks);
  const isRunning = task.status === 'in_progress';
  const needsReview = task.status === 'human_review';
  const executionPhase = task.executionProgress?.phase;
  const hasActiveExecution = executionPhase && executionPhase !== 'idle' && executionPhase !== 'complete' && executionPhase !== 'failed';

  // Disable editing when task is actively running
  const canEdit = !isRunning || isStuck;

  // Sync edit fields when task changes (e.g., from external updates)
  useEffect(() => {
    if (!isEditMode) {
      setEditTitle(task.title);
      setEditDescription(task.description);
    }
  }, [task.title, task.description, isEditMode]);

  // Check if task is stuck (status says in_progress but no actual process)
  useEffect(() => {
    if (isRunning && !hasCheckedRunning) {
      checkTaskRunning(task.id).then((actuallyRunning) => {
        setIsStuck(!actuallyRunning);
        setHasCheckedRunning(true);
      });
    } else if (!isRunning) {
      setIsStuck(false);
      setHasCheckedRunning(false);
    }
  }, [task.id, isRunning, hasCheckedRunning]);

  // Handle scroll events in logs to detect if user scrolled up
  const handleLogsScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const isNearBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 100;
    setIsUserScrolledUp(!isNearBottom);
  };

  // Auto-scroll logs to bottom only if user hasn't scrolled up
  useEffect(() => {
    if (activeTab === 'logs' && logsEndRef.current && !isUserScrolledUp) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [task.logs, activeTab, isUserScrolledUp]);

  // Reset scroll state when switching to logs tab
  useEffect(() => {
    if (activeTab === 'logs') {
      setIsUserScrolledUp(false);
    }
  }, [activeTab]);

  const handleStartStop = () => {
    if (isRunning && !isStuck) {
      stopTask(task.id);
    } else {
      startTask(task.id);
    }
  };

  const handleRecover = async () => {
    setIsRecovering(true);
    const result = await recoverStuckTask(task.id, 'backlog');
    if (result.success) {
      setIsStuck(false);
    }
    setIsRecovering(false);
  };

  const handleApprove = async () => {
    setIsSubmitting(true);
    await submitReview(task.id, true);
    setIsSubmitting(false);
    onClose();
  };

  const handleReject = async () => {
    if (!feedback.trim()) {
      return;
    }
    setIsSubmitting(true);
    await submitReview(task.id, false, feedback);
    setIsSubmitting(false);
    setFeedback('');
  };

  const handleEditClick = () => {
    setEditTitle(task.title);
    setEditDescription(task.description);
    setIsEditMode(true);
  };

  const handleCancelEdit = () => {
    setEditTitle(task.title);
    setEditDescription(task.description);
    setIsEditMode(false);
  };

  const handleSaveEdit = async () => {
    // Don't save if nothing changed
    if (editTitle === task.title && editDescription === task.description) {
      setIsEditMode(false);
      return;
    }

    // Validate - title is required
    if (!editTitle.trim()) {
      return;
    }

    setIsSaving(true);
    const result = await persistUpdateTask(task.id, {
      title: editTitle.trim(),
      description: editDescription.trim()
    });

    if (result) {
      setIsEditMode(false);
    }
    setIsSaving(false);
  };

  const getChunkStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-[var(--info)] animate-pulse" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-[var(--error)]" />;
      default:
        return <AlertCircle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="flex h-full w-96 flex-col bg-card border-l border-border">
      {/* Header */}
      <div className="flex items-start justify-between p-4">
        <div className="flex-1 min-w-0 pr-2">
          {isEditMode ? (
            <Input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="font-semibold text-lg h-auto py-1"
              placeholder="Task title"
              autoFocus
            />
          ) : (
            <h2 className="font-semibold text-lg text-foreground truncate">{task.title}</h2>
          )}
          <div className="mt-1.5 flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {task.specId}
            </Badge>
            {isStuck ? (
              <Badge variant="warning" className="text-xs flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Stuck
              </Badge>
            ) : (
              <span className="text-xs text-muted-foreground">
                {TASK_STATUS_LABELS[task.status]}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!isEditMode && canEdit && (
            <Button variant="ghost" size="icon" onClick={handleEditClick} title="Edit task">
              <Pencil className="h-4 w-4" />
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Separator />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <TabsList className="w-full justify-start rounded-none border-b border-border bg-transparent p-0 h-auto">
          <TabsTrigger
            value="overview"
            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-2.5 text-sm"
          >
            Overview
          </TabsTrigger>
          <TabsTrigger
            value="chunks"
            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-2.5 text-sm"
          >
            Chunks ({task.chunks.length})
          </TabsTrigger>
          <TabsTrigger
            value="logs"
            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-2.5 text-sm"
          >
            Logs
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="flex-1 min-h-0 overflow-hidden mt-0">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-5">
              {/* Stuck Task Warning */}
              {isStuck && (
                <div className="rounded-xl border border-warning/30 bg-warning/10 p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-warning shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <h3 className="font-medium text-sm text-foreground mb-1">
                        Task Appears Stuck
                      </h3>
                      <p className="text-sm text-muted-foreground mb-3">
                        This task is marked as running but no active process was found.
                        This can happen if the app crashed or the process was terminated unexpectedly.
                      </p>
                      <Button
                        variant="warning"
                        size="sm"
                        onClick={handleRecover}
                        disabled={isRecovering}
                        className="w-full"
                      >
                        {isRecovering ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Recovering...
                          </>
                        ) : (
                          <>
                            <RotateCcw className="mr-2 h-4 w-4" />
                            Recover Task (Move to Planning)
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Execution Phase Indicator */}
              {hasActiveExecution && executionPhase && !isStuck && (
                <div className={cn(
                  'rounded-xl border p-3 flex items-center gap-3',
                  EXECUTION_PHASE_BADGE_COLORS[executionPhase]
                )}>
                  <Loader2 className="h-5 w-5 animate-spin shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {EXECUTION_PHASE_LABELS[executionPhase]}
                      </span>
                      <span className="text-sm">
                        {task.executionProgress?.overallProgress || 0}%
                      </span>
                    </div>
                    {task.executionProgress?.message && (
                      <p className="text-xs mt-0.5 opacity-80 truncate">
                        {task.executionProgress.message}
                      </p>
                    )}
                    {task.executionProgress?.currentChunk && (
                      <p className="text-xs mt-0.5 opacity-70">
                        Chunk: {task.executionProgress.currentChunk}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Progress */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">
                    {hasActiveExecution ? 'Overall Progress' : 'Progress'}
                  </span>
                  <span className="text-sm text-foreground">
                    {hasActiveExecution
                      ? `${task.executionProgress?.overallProgress || 0}%`
                      : `${progress}%`}
                  </span>
                </div>
                <Progress
                  value={hasActiveExecution ? (task.executionProgress?.overallProgress || 0) : progress}
                  className="h-2"
                />
                {/* Phase Progress Bar Segments */}
                {hasActiveExecution && (
                  <div className="mt-2 flex gap-0.5 h-1.5 rounded-full overflow-hidden bg-muted/30">
                    <div
                      className={cn(
                        'transition-all duration-300',
                        executionPhase === 'planning' ? 'bg-amber-500' : 'bg-amber-500/30'
                      )}
                      style={{ width: '20%' }}
                      title="Planning (0-20%)"
                    />
                    <div
                      className={cn(
                        'transition-all duration-300',
                        executionPhase === 'coding' ? 'bg-info' : 'bg-info/30'
                      )}
                      style={{ width: '60%' }}
                      title="Coding (20-80%)"
                    />
                    <div
                      className={cn(
                        'transition-all duration-300',
                        (executionPhase === 'qa_review' || executionPhase === 'qa_fixing') ? 'bg-purple-500' : 'bg-purple-500/30'
                      )}
                      style={{ width: '15%' }}
                      title="AI Review (80-95%)"
                    />
                    <div
                      className={cn(
                        'transition-all duration-300',
                        executionPhase === 'complete' ? 'bg-success' : 'bg-success/30'
                      )}
                      style={{ width: '5%' }}
                      title="Complete (95-100%)"
                    />
                  </div>
                )}
              </div>

              {/* Classification Badges */}
              {task.metadata && (
                <div className="flex flex-wrap gap-1.5">
                  {/* Category */}
                  {task.metadata.category && (
                    <Badge
                      variant="outline"
                      className={cn('text-xs', TASK_CATEGORY_COLORS[task.metadata.category])}
                    >
                      {CategoryIcon[task.metadata.category] && (() => {
                        const Icon = CategoryIcon[task.metadata.category!];
                        return <Icon className="h-3 w-3 mr-1" />;
                      })()}
                      {TASK_CATEGORY_LABELS[task.metadata.category]}
                    </Badge>
                  )}
                  {/* Priority */}
                  {task.metadata.priority && (
                    <Badge
                      variant="outline"
                      className={cn('text-xs', TASK_PRIORITY_COLORS[task.metadata.priority])}
                    >
                      {TASK_PRIORITY_LABELS[task.metadata.priority]}
                    </Badge>
                  )}
                  {/* Complexity */}
                  {task.metadata.complexity && (
                    <Badge
                      variant="outline"
                      className={cn('text-xs', TASK_COMPLEXITY_COLORS[task.metadata.complexity])}
                    >
                      {TASK_COMPLEXITY_LABELS[task.metadata.complexity]}
                    </Badge>
                  )}
                  {/* Impact */}
                  {task.metadata.impact && (
                    <Badge
                      variant="outline"
                      className={cn('text-xs', TASK_IMPACT_COLORS[task.metadata.impact])}
                    >
                      {TASK_IMPACT_LABELS[task.metadata.impact]}
                    </Badge>
                  )}
                  {/* Security Severity */}
                  {task.metadata.securitySeverity && (
                    <Badge
                      variant="outline"
                      className={cn('text-xs', TASK_IMPACT_COLORS[task.metadata.securitySeverity])}
                    >
                      <Shield className="h-3 w-3 mr-1" />
                      {task.metadata.securitySeverity} severity
                    </Badge>
                  )}
                  {/* Source Type */}
                  {task.metadata.sourceType && (
                    <Badge variant="secondary" className="text-xs">
                      {task.metadata.sourceType === 'ideation' && task.metadata.ideationType
                        ? IDEATION_TYPE_LABELS[task.metadata.ideationType] || task.metadata.ideationType
                        : task.metadata.sourceType}
                    </Badge>
                  )}
                </div>
              )}

              {/* Description */}
              {isEditMode ? (
                <div>
                  <h3 className="text-sm font-medium text-foreground mb-2">Description</h3>
                  <Textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="text-sm min-h-[100px]"
                    placeholder="Task description (optional)"
                    rows={4}
                  />
                </div>
              ) : task.description ? (
                <div>
                  <h3 className="text-sm font-medium text-foreground mb-2">Description</h3>
                  <p className="text-sm text-muted-foreground">{task.description}</p>
                </div>
              ) : null}

              {/* Metadata Details */}
              {task.metadata && (
                <div className="space-y-4">
                  {/* Rationale */}
                  {task.metadata.rationale && (
                    <div>
                      <h3 className="text-sm font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                        <Lightbulb className="h-3.5 w-3.5 text-warning" />
                        Rationale
                      </h3>
                      <p className="text-sm text-muted-foreground">{task.metadata.rationale}</p>
                    </div>
                  )}

                  {/* Problem Solved */}
                  {task.metadata.problemSolved && (
                    <div>
                      <h3 className="text-sm font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                        <Target className="h-3.5 w-3.5 text-success" />
                        Problem Solved
                      </h3>
                      <p className="text-sm text-muted-foreground">{task.metadata.problemSolved}</p>
                    </div>
                  )}

                  {/* Target Audience */}
                  {task.metadata.targetAudience && (
                    <div>
                      <h3 className="text-sm font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                        <Users className="h-3.5 w-3.5 text-info" />
                        Target Audience
                      </h3>
                      <p className="text-sm text-muted-foreground">{task.metadata.targetAudience}</p>
                    </div>
                  )}

                  {/* Dependencies */}
                  {task.metadata.dependencies && task.metadata.dependencies.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                        <GitBranch className="h-3.5 w-3.5 text-purple-400" />
                        Dependencies
                      </h3>
                      <ul className="text-sm text-muted-foreground list-disc list-inside space-y-0.5">
                        {task.metadata.dependencies.map((dep, idx) => (
                          <li key={idx}>{dep}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Acceptance Criteria */}
                  {task.metadata.acceptanceCriteria && task.metadata.acceptanceCriteria.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                        <ListChecks className="h-3.5 w-3.5 text-success" />
                        Acceptance Criteria
                      </h3>
                      <ul className="text-sm text-muted-foreground list-disc list-inside space-y-0.5">
                        {task.metadata.acceptanceCriteria.map((criteria, idx) => (
                          <li key={idx}>{criteria}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Affected Files */}
                  {task.metadata.affectedFiles && task.metadata.affectedFiles.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                        <FileCode className="h-3.5 w-3.5 text-muted-foreground" />
                        Affected Files
                      </h3>
                      <div className="flex flex-wrap gap-1">
                        {task.metadata.affectedFiles.map((file, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs font-mono">
                            {file.split('/').pop()}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Attached Images */}
                  {task.metadata.attachedImages && task.metadata.attachedImages.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                        <ImageIcon className="h-3.5 w-3.5 text-info" />
                        Attached Images ({task.metadata.attachedImages.length})
                      </h3>
                      <div className="grid grid-cols-2 gap-2">
                        {task.metadata.attachedImages.map((image) => (
                          <div
                            key={image.id}
                            className="rounded-lg border border-border bg-muted/30 p-2 space-y-1"
                          >
                            <div className="flex items-center gap-2">
                              <ImageIcon className="h-4 w-4 text-muted-foreground shrink-0" />
                              <span className="text-xs font-medium text-foreground truncate">
                                {image.filename}
                              </span>
                            </div>
                            {image.path && (
                              <p className="text-[10px] text-muted-foreground font-mono truncate">
                                {image.path}
                              </p>
                            )}
                            <p className="text-[10px] text-muted-foreground">
                              {image.size < 1024
                                ? `${image.size} B`
                                : image.size < 1024 * 1024
                                  ? `${(image.size / 1024).toFixed(1)} KB`
                                  : `${(image.size / (1024 * 1024)).toFixed(1)} MB`}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Timestamps */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Created</span>
                  <span className="text-foreground">{formatRelativeTime(task.createdAt)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Updated</span>
                  <span className="text-foreground">{formatRelativeTime(task.updatedAt)}</span>
                </div>
              </div>

              {/* Edit Mode Save/Cancel Buttons */}
              {isEditMode && (
                <div className="flex gap-2">
                  <Button
                    variant="default"
                    onClick={handleSaveEdit}
                    disabled={isSaving || !editTitle.trim()}
                    className="flex-1"
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Save Changes
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleCancelEdit}
                    disabled={isSaving}
                    className="flex-1"
                  >
                    <X className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                </div>
              )}

              {/* Human Review Section */}
              {needsReview && !isEditMode && (
                <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 p-4">
                  <h3 className="font-medium text-sm text-foreground mb-2 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-purple-400" />
                    Review Required
                  </h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Please review the changes and provide feedback if needed.
                  </p>
                  <Textarea
                    placeholder="Enter feedback for rejection (optional for approval)..."
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    className="mb-3"
                    rows={3}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="success"
                      onClick={handleApprove}
                      disabled={isSubmitting}
                      className="flex-1"
                    >
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      Approve
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={handleReject}
                      disabled={isSubmitting || !feedback.trim()}
                      className="flex-1"
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Chunks Tab */}
        <TabsContent value="chunks" className="flex-1 min-h-0 overflow-hidden mt-0">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-3">
              {task.chunks.length === 0 ? (
                <div className="text-center text-sm text-muted-foreground py-8">
                  No chunks defined yet
                </div>
              ) : (
                task.chunks.map((chunk, index) => (
                  <div
                    key={chunk.id}
                    className={cn(
                      'rounded-xl border border-border bg-secondary/30 p-3 transition-all duration-200',
                      chunk.status === 'in_progress' && 'border-[var(--info)]/50 bg-[var(--info-light)]',
                      chunk.status === 'completed' && 'border-[var(--success)]/50 bg-[var(--success-light)]',
                      chunk.status === 'failed' && 'border-[var(--error)]/50 bg-[var(--error-light)]'
                    )}
                  >
                    <div className="flex items-start gap-2">
                      {getChunkStatusIcon(chunk.status)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            #{index + 1}
                          </span>
                          <span className="text-sm font-medium text-foreground truncate">
                            {chunk.id}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                          {chunk.description}
                        </p>
                        {chunk.files && chunk.files.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {chunk.files.map((file) => (
                              <Badge
                                key={file}
                                variant="secondary"
                                className="text-xs"
                              >
                                <FileCode className="mr-1 h-3 w-3" />
                                {file.split('/').pop()}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="flex-1 min-h-0 overflow-hidden mt-0">
          <div
            ref={logsContainerRef}
            className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
            onScroll={handleLogsScroll}
          >
            <div className="p-4">
              {task.logs && task.logs.length > 0 ? (
                <pre className="text-xs font-mono text-muted-foreground whitespace-pre-wrap break-all">
                  {task.logs.join('')}
                  <div ref={logsEndRef} />
                </pre>
              ) : (
                <div className="text-center text-sm text-muted-foreground py-8">
                  <Terminal className="mx-auto mb-2 h-8 w-8 opacity-50" />
                  <p>No logs yet</p>
                  <p className="text-xs mt-1">Logs will appear here when the task runs</p>
                </div>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <Separator />

      {/* Actions */}
      <div className="p-4">
        {isStuck ? (
          <Button
            className="w-full"
            variant="warning"
            onClick={handleRecover}
            disabled={isRecovering}
          >
            {isRecovering ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Recovering...
              </>
            ) : (
              <>
                <RotateCcw className="mr-2 h-4 w-4" />
                Recover Task
              </>
            )}
          </Button>
        ) : (task.status === 'backlog' || task.status === 'in_progress') && (
          <Button
            className="w-full"
            variant={isRunning ? 'destructive' : 'default'}
            onClick={handleStartStop}
          >
            {isRunning ? (
              <>
                <Square className="mr-2 h-4 w-4" />
                Stop Task
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Start Task
              </>
            )}
          </Button>
        )}
        {task.status === 'done' && (
          <div className="text-center text-sm text-[var(--success)]">
            <CheckCircle2 className="mx-auto mb-1 h-6 w-6" />
            Task completed successfully
          </div>
        )}
      </div>
    </div>
  );
}
