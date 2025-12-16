"""CCS-aware executor for intelligent model switching"""

import asyncio
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Union
from enum import Enum

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError,
    AssistantMessage,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    TextBlock,
)
from sleepless_agent.monitoring.logging import get_logger

logger = get_logger(__name__)

from sleepless_agent.utils.live_status import LiveStatusEntry, LiveStatusTracker
from sleepless_agent.core.executor import ClaudeCodeExecutor


class ModelPhase(Enum):
    """Phases of task execution"""
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"


class CCSModel(Enum):
    """Supported models via CCS"""
    DEFAULT = "default"  # Default Claude Code account
    GLM = "glm"          # GLM for cost-effective execution


class TaskRouter:
    """Intelligent router for selecting optimal model per task phase"""

    def __init__(self, config: dict):
        """Initialize router with configuration"""
        self.config = config
        self.model_costs = {
            CCSModel.DEFAULT: 0.015,  # $15 per 1M tokens
            CCSModel.GLM: 0.0005,   # $0.50 per 1M tokens
        }

    def select_model(self, phase: ModelPhase, task_description: str,
                    task_priority: str = "thought") -> CCSModel:
        """Select optimal model based on phase and task characteristics"""

        # High-value phases always use Claude
        if phase in [ModelPhase.PLANNING, ModelPhase.REVIEW]:
            return CCSModel.DEFAULT

        # Execution phase model selection
        if phase == ModelPhase.EXECUTION:
            # Check for specific task patterns
            desc_lower = task_description.lower()

            # Complex tasks that need Claude's reasoning
            complex_patterns = [
                "architecture", "design system", "algorithm", "optimize",
                "debug complex", "security", "performance critical"
            ]
            if any(pattern in desc_lower for pattern in complex_patterns):
                return CCSModel.DEFAULT

            # Bulk/routine tasks perfect for GLM
            routine_patterns = [
                "implement", "add feature", "write tests", "documentation",
                "refactor", "update", "migration", "boilerplate"
            ]
            if any(pattern in desc_lower for pattern in routine_patterns):
                return CCSModel.GLM

            # Default to GLM for cost efficiency
            return CCSModel.GLM

        # Default fallback
        return CCSModel.DEFAULT

    def get_model_config(self, model: CCSModel) -> dict:
        """Get model-specific configuration"""
        return self.config.get("ccs", {}).get("models", {}).get(model.value, {})

    def estimate_cost(self, model: CCSModel, estimated_tokens: int) -> float:
        """Estimate cost for model usage"""
        return (estimated_tokens / 1_000_000) * self.model_costs[model]


class CCSAwareExecutor(ClaudeCodeExecutor):
    """Claude Code executor with CCS integration for intelligent model switching"""

    def __init__(
        self,
        workspace_root: str = "./workspace",
        default_timeout: int = 3600,
        live_status_tracker: Optional[LiveStatusTracker] = None,
        default_model: str = "claude-sonnet-4-5-20250929",
        enable_ccs: bool = True,
        ccs_config: Optional[dict] = None,
    ):
        """Initialize CCS-aware executor

        Args:
            workspace_root: Root directory for task workspaces
            default_timeout: Default timeout in seconds
            live_status_tracker: Live status tracker instance
            default_model: Default model for non-CCS execution
            enable_ccs: Whether to use CCS for model switching
            ccs_config: CCS configuration dict
        """
        # Initialize parent class but we'll override the CLI command
        super().__init__(
            workspace_root=workspace_root,
            default_timeout=default_timeout,
            live_status_tracker=live_status_tracker,
            default_model=default_model,
        )

        self.enable_ccs = enable_ccs
        self.ccs_config = ccs_config or {}
        self.task_router = TaskRouter(self.ccs_config)

        # Track model usage for cost analysis
        self.model_usage = {
            model.value: {"requests": 0, "tokens": 0, "cost": 0.0}
            for model in CCSModel
        }

        # Verify CCS is available if enabled
        if self.enable_ccs:
            self._verify_ccs_cli()

        logger.info("ccs_executor.init",
                   ccs_enabled=self.enable_ccs,
                   binary_path=self.ccs_config.get("binary_path", "ccs"))

    def _verify_ccs_cli(self):
        """Verify CCS CLI is available"""
        try:
            ccs_binary = self.ccs_config.get("binary_path", "ccs")
            result = subprocess.run(
                [ccs_binary, "--version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.debug("ccs_executor.cli.verified")
            else:
                logger.warning("ccs_executor.cli.not_found", falling_back=True)
                self.enable_ccs = False

        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ccs_executor.cli.not_found", falling_back=True)
            self.enable_ccs = False
        except Exception as e:
            logger.warning("ccs_executor.cli.verify_failed", error=str(e))
            self.enable_ccs = False

    def _get_cli_command(self, model: CCSModel) -> List[str]:
        """Get the CLI command for a specific model"""
        if not self.enable_ccs:
            return ["claude"]

        # For DEFAULT model, use direct Claude CLI
        if model == CCSModel.DEFAULT:
            model_config = self.task_router.get_model_config(model)
            if model_config.get("use_direct_claude", False):
                return ["claude"]

        ccs_binary = self.ccs_config.get("binary_path", "ccs")
        model_config = self.task_router.get_model_config(model)

        # Build CCS command
        cmd = [ccs_binary]

        # Add model-specific flags
        if model == CCSModel.GLM:
            cmd.append("glm")

        # Add any additional flags from config
        additional_flags = model_config.get("flags", [])
        cmd.extend(additional_flags)

        return cmd

    async def _execute_with_model(
        self,
        model: CCSModel,
        prompt: str,
        options: ClaudeAgentOptions,
        task_id: int,
        phase: str,
    ) -> Tuple[str, dict]:
        """Execute prompt with specific model via CCS"""

        # Track model usage
        self.model_usage[model.value]["requests"] += 1

        # Get CLI command for this model
        cli_cmd = self._get_cli_command(model)

        # Modify options to use the specific CLI command
        # Note: claude_agent_sdk might need modifications to support custom CLI paths
        # For now, we'll use environment variable to override
        env = os.environ.copy()
        env["CLAUDE_BINARY"] = " ".join(cli_cmd)

        usage_metrics = {
            f"{phase}_cost_usd": None,
            f"{phase}_duration_ms": None,
            f"{phase}_turns": None,
            f"{phase}_model": model.value,
        }

        try:
            output_parts = []
            start_time = time.time()

            self._live_update(
                task_id,
                phase=phase,
                prompt=prompt[:500] if prompt else "",
                answer="",
                status="running",
            )

            # Execute with the specific model
            # Note: This assumes claude_agent_sdk respects CLAUDE_BINARY env var
            # If not, we might need to use subprocess directly
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text = block.text.strip()
                            if text:
                                output_parts.append(text)
                                self._live_update(
                                    task_id,
                                    phase=phase,
                                    prompt=prompt[:500] if prompt else "",
                                    answer=text,
                                    status="running",
                                )

                elif isinstance(message, ResultMessage):
                    usage_metrics[f"{phase}_cost_usd"] = message.total_cost_usd
                    usage_metrics[f"{phase}_duration_ms"] = message.duration_ms
                    usage_metrics[f"{phase}_turns"] = message.num_turns

                    # Update model usage tracking
                    if message.total_cost_usd:
                        self.model_usage[model.value]["cost"] += message.total_cost_usd

                    logger.debug(
                        f"ccs_executor.{phase}.turn_metrics",
                        model=model.value,
                        duration_ms=message.duration_ms,
                        turns=message.num_turns,
                        cost_usd=message.total_cost_usd,
                    )

            output_text = "\n".join(output_parts)

            self._live_update(
                task_id,
                phase=phase,
                prompt=prompt[:500] if prompt else "",
                answer=output_text,
                status="completed",
            )

            return output_text, usage_metrics

        except Exception as e:
            logger.error(f"ccs_executor.{phase}.failed",
                        model=model.value, error=str(e))
            raise

    async def _execute_planner_phase(
        self,
        task_id: int,
        workspace: Path,
        description: str,
        context: str,
        config_max_turns: int = 10,
        workspace_task_type: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """Execute planner phase with optimal model"""

        # Always use DEFAULT (Claude) for planning (high-value reasoning)
        model = CCSModel.DEFAULT if self.enable_ccs else None

        # Reuse parent logic but with model switching
        if self.enable_ccs and model:
            # Get allowed directories
            allowed_dirs = self._get_allowed_directories(
                workspace=workspace,
                workspace_task_type=workspace_task_type,
                project_id=project_id,
            )

            # Build planner prompt
            task_type_note = ""
            if workspace_task_type == "refine":
                task_type_note = """
## 🔧 REFINE TASK
This workspace contains a copy of the sleepless-agent source code. Your goal is to IMPROVE the existing codebase:
- Analyze and understand the current implementation
- Refactor, optimize, or enhance existing code
- Fix bugs or issues
- Improve code quality, tests, or documentation
- Add missing features to existing modules
"""
            elif workspace_task_type == "new":
                task_type_note = """
## 🆕 NEW TASK
This is a fresh workspace. Your goal is to BUILD new functionality from scratch:
- Design and implement new features
- Create new modules or tools
- Build standalone projects or prototypes
- Experiment with new ideas
"""

            planner_prompt = f"""You are a planning expert. Analyze the task and workspace context, then create a structured plan.
{task_type_note}
## Task
{description}

## Workspace Context
{context}

## Your Task
1. Analyze the task requirements and workspace
2. Identify what needs to be done
3. Create a detailed TODO list with specific, actionable items
4. Note any dependencies between tasks
5. Estimate effort level for each TODO item
6. Suggest which subtasks should be executed with cost-effective models (GLM) vs high-quality models (Claude)

Output should be:
- Executive summary (2-3 sentences)
- Analysis of the task
- Structured TODO list (numbered, with clear descriptions and effort levels)
- Notes on approach and strategy
- Model allocation recommendations (which tasks can use GLM vs need Claude)
- Any assumptions or potential blockers
"""

            # Get CLI command for model
            cli_cmd = self._get_cli_command(model)

            options = ClaudeAgentOptions(
                cwd=str(workspace),
                add_dirs=allowed_dirs,
                allowed_tools=["Read", "Glob", "Grep"],
                permission_mode="acceptEdits",
                max_turns=config_max_turns,
                model=self.default_model,
            )

            # Execute with the selected model
            return await self._execute_with_model(
                model=model,
                prompt=planner_prompt,
                options=options,
                task_id=task_id,
                phase="planner",
            )
        else:
            # Fallback to parent implementation
            return await super()._execute_planner_phase(
                task_id=task_id,
                workspace=workspace,
                description=description,
                context=context,
                config_max_turns=config_max_turns,
                workspace_task_type=workspace_task_type,
                project_id=project_id,
            )

    async def _execute_worker_phase(
        self,
        task_id: int,
        workspace: Path,
        description: str,
        plan_text: str,
        config_max_turns: int = 30,
        workspace_task_type: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[str, set, list, int, dict]:
        """Execute worker phase with intelligent model selection"""

        # Select optimal model for execution
        model = None
        if self.enable_ccs:
            model = self.task_router.select_model(
                phase=ModelPhase.EXECUTION,
                task_description=description,
            )

        if self.enable_ccs and model:
            # Get allowed directories
            allowed_dirs = self._get_allowed_directories(
                workspace=workspace,
                workspace_task_type=workspace_task_type,
                project_id=project_id,
            )

            # Enhance worker prompt based on selected model
            model_note = ""
            if model == CCSModel.GLM:
                model_note = """
## 💰 Cost-Optimized Execution (GLM)
You are running on a cost-effective model (GLM). Focus on:
- Efficient implementation
- Clear, straightforward code
- Following the plan precisely
- Avoid unnecessary complexity
"""
            elif model == CCSModel.CLAUDE:
                model_note = """
## 🧠 High-Quality Execution (Claude)
You are running on a premium model (Claude Sonnet 4.5). Focus on:
- Optimal solutions and best practices
- Comprehensive implementation
- Error handling and edge cases
- Code quality and maintainability
"""

            worker_prompt = f"""You are an expert developer/engineer. Execute the plan below to complete the task.
{model_note}
## Task
{description}

## Plan to Execute
{plan_text}

## Instructions
1. Execute the TODO items from the plan
2. Use TodoWrite to track progress on each item
3. Make changes using available tools (Read, Write, Edit, Bash)
4. Test your changes as needed
5. Provide a summary of what you completed
6. Note any deviations from the plan or blockers encountered

Please work through the plan systematically and update TodoWrite as you complete each item.
"""

            # Track files and commands
            files_modified = set()
            commands_executed = []
            output_parts = []
            usage_metrics = {
                "worker_cost_usd": None,
                "worker_duration_ms": None,
                "worker_turns": None,
                "worker_model": model.value,
            }

            try:
                files_before = self._get_workspace_files(workspace)

                self._live_update(
                    task_id,
                    phase="worker",
                    prompt=worker_prompt[:500] if worker_prompt else "",
                    answer="",
                    status="running",
                )

                # Get CLI command
                cli_cmd = self._get_cli_command(model)

                options = ClaudeAgentOptions(
                    cwd=str(workspace),
                    add_dirs=allowed_dirs,
                    allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "TodoWrite"],
                    permission_mode="acceptEdits",
                    max_turns=config_max_turns,
                    model=self.default_model,
                )

                # Execute with model tracking
                async for message in query(prompt=worker_prompt, options=options):
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                text = block.text.strip()
                                if text:
                                    output_parts.append(text)
                                    self._live_update(
                                        task_id,
                                        phase="worker",
                                        prompt=worker_prompt[:500] if worker_prompt else "",
                                        answer=text,
                                        status="running",
                                    )
                            elif isinstance(block, ToolUseBlock):
                                tool_name = block.name

                                if tool_name in ["Write", "Edit"]:
                                    file_path = block.input.get("file_path", "")
                                    if file_path:
                                        files_modified.add(file_path)

                                elif tool_name == "Bash":
                                    command = block.input.get("command", "")
                                    if command:
                                        commands_executed.append(command)

                    elif isinstance(message, ResultMessage):
                        success = not message.is_error
                        if message.result:
                            output_parts.append(f"\n[Result: {message.result}]")

                        usage_metrics["worker_cost_usd"] = message.total_cost_usd
                        usage_metrics["worker_duration_ms"] = message.duration_ms
                        usage_metrics["worker_turns"] = message.num_turns

                        # Update model usage
                        if message.total_cost_usd:
                            self.model_usage[model.value]["cost"] += message.total_cost_usd

                output_text = "\n".join(output_parts)
                files_after = self._get_workspace_files(workspace)
                new_files = files_after - files_before
                all_modified_files = files_modified.union(new_files)

                exit_code = 0 if success else 1

                self._live_update(
                    task_id,
                    phase="worker",
                    prompt=worker_prompt[:500] if worker_prompt else "",
                    answer=output_text,
                    status="completed" if exit_code == 0 else "error",
                )

                return output_text, all_modified_files, commands_executed, exit_code, usage_metrics

            except Exception as e:
                logger.error("ccs_executor.worker.failed", model=model.value, error=str(e))
                raise
        else:
            # Fallback to parent implementation
            return await super()._execute_worker_phase(
                task_id=task_id,
                workspace=workspace,
                description=description,
                plan_text=plan_text,
                config_max_turns=config_max_turns,
                workspace_task_type=workspace_task_type,
                project_id=project_id,
            )

    async def _execute_evaluator_phase(
        self,
        task_id: int,
        workspace: Path,
        description: str,
        plan_text: str,
        worker_output: str,
        files_modified: set,
        commands_executed: list,
        config_max_turns: int = 10,
        workspace_task_type: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[str, str, list, list, dict]:
        """Execute evaluator phase with optimal model"""

        # Always use DEFAULT (Claude) for evaluation (high-quality review)
        model = CCSModel.DEFAULT if self.enable_ccs else None

        if self.enable_ccs and model:
            # Get allowed directories
            allowed_dirs = self._get_allowed_directories(
                workspace=workspace,
                workspace_task_type=workspace_task_type,
                project_id=project_id,
            )

            evaluator_prompt = f"""You are a quality assurance expert. Evaluate whether the task was completed successfully.

## Task
{description}

## Original Plan
{plan_text}

## Worker Output
{worker_output}

## Changes Made
- Files Modified: {len(files_modified)}
- Commands Executed: {len(commands_executed)}

## Your Task
1. Review the worker output against the original plan
2. Verify each TODO item was addressed
3. Check if the task objectives were met
4. Identify any incomplete items or issues
5. Provide a comprehensive evaluation summary
6. Assess if the appropriate model was used for each subtask
7. Note any quality differences between model executions

Output should include:
- Completion status (COMPLETE / INCOMPLETE / PARTIAL)
- Items successfully completed
- Any outstanding items
- Quality assessment
- Model usage effectiveness review
- Recommendations (if any)
"""

            # Execute with Claude
            eval_text, metrics = await self._execute_with_model(
                model=model,
                prompt=evaluator_prompt,
                options=ClaudeAgentOptions(
                    cwd=str(workspace),
                    add_dirs=allowed_dirs,
                    allowed_tools=["Read", "Glob"],
                    permission_mode="acceptEdits",
                    max_turns=config_max_turns,
                    model=self.default_model,
                ),
                task_id=task_id,
                phase="evaluator",
            )

            # Extract evaluation status
            status = self._extract_status_from_evaluation(eval_text)
            outstanding_items = self._extract_outstanding_items(eval_text)
            recommendations = self._extract_recommendations(eval_text)

            # Add model usage info to metrics
            metrics["evaluator_model"] = model.value

            return eval_text, status, outstanding_items, recommendations, metrics
        else:
            # Fallback to parent implementation
            return await super()._execute_evaluator_phase(
                task_id=task_id,
                workspace=workspace,
                description=description,
                plan_text=plan_text,
                worker_output=worker_output,
                files_modified=files_modified,
                commands_executed=commands_executed,
                config_max_turns=config_max_turns,
                workspace_task_type=workspace_task_type,
                project_id=project_id,
            )

    def get_model_usage_stats(self) -> dict:
        """Get model usage statistics"""
        total_cost = sum(stats["cost"] for stats in self.model_usage.values())
        total_requests = sum(stats["requests"] for stats in self.model_usage.values())

        return {
            "total_cost_usd": total_cost,
            "total_requests": total_requests,
            "model_breakdown": self.model_usage.copy(),
            "cost_savings": self._calculate_cost_savings(),
        }

    def _calculate_cost_savings(self) -> dict:
        """Calculate cost savings compared to using Claude for everything"""
        claude_only_cost = 0
        actual_cost = 0

        for model, stats in self.model_usage.items():
            if stats["requests"] > 0:
                # Estimate what this would have cost with Claude
                estimated_tokens = 1000  # Rough estimate
                claude_cost = (estimated_tokens / 1_000_000) * 0.015 * stats["requests"]
                claude_only_cost += claude_cost
                actual_cost += stats["cost"]

        savings = claude_only_cost - actual_cost
        savings_percent = (savings / claude_only_cost * 100) if claude_only_cost > 0 else 0

        return {
            "estimated_claude_only_cost": claude_only_cost,
            "actual_cost": actual_cost,
            "savings_usd": savings,
            "savings_percent": savings_percent,
        }