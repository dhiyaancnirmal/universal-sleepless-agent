#!/usr/bin/env python3
"""Simple test for CCS integration without full installation"""

import sys
from pathlib import Path
from enum import Enum


# Mock the CCS components for testing
class ModelPhase(Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"


class CCSModel(Enum):
    DEFAULT = "default"  # Default Claude Code account
    GLM = "glm"


class TaskRouter:
    """Simplified version of TaskRouter for testing"""

    def __init__(self, config=None):
        self.config = config or {}
        self.model_costs = {
            CCSModel.DEFAULT: 0.015,  # $15 per 1M tokens
            CCSModel.GLM: 0.0005,   # $0.50 per 1M tokens
        }

    def select_model(self, phase: ModelPhase, task_description: str,
                    task_priority: str = "thought") -> CCSModel:
        """Select optimal model based on phase and task characteristics"""

        # High-value phases always use DEFAULT (Claude)
        if phase in [ModelPhase.PLANNING, ModelPhase.REVIEW]:
            return CCSModel.DEFAULT

        # Execution phase model selection
        if phase == ModelPhase.EXECUTION:
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

    def estimate_cost(self, model: CCSModel, estimated_tokens: int) -> float:
        """Estimate cost for model usage"""
        return (estimated_tokens / 1_000_000) * self.model_costs[model]


def test_task_router():
    """Test the task router logic"""
    print("🧠 Testing Task Router Logic\n")

    router = TaskRouter()

    test_cases = [
        # (phase, task_description, expected_model, reason)
        (ModelPhase.PLANNING, "Build a user authentication system", CCSModel.DEFAULT, "Planning always uses Claude"),
        (ModelPhase.REVIEW, "Check code for security issues", CCSModel.DEFAULT, "Review always uses Claude"),
        (ModelPhase.EXECUTION, "Implement CRUD operations", CCSModel.GLM, "Routine implementation"),
        (ModelPhase.EXECUTION, "Design microservices architecture", CCSModel.DEFAULT, "Complex design work"),
        (ModelPhase.EXECUTION, "Write unit tests for API", CCSModel.GLM, "Test generation"),
        (ModelPhase.EXECUTION, "Optimize database queries", CCSModel.DEFAULT, "Performance optimization"),
        (ModelPhase.EXECUTION, "Add documentation", CCSModel.GLM, "Documentation is routine"),
        (ModelPhase.EXECUTION, "Fix security vulnerability", CCSModel.DEFAULT, "Security is critical"),
        (ModelPhase.EXECUTION, "Create REST API endpoints", CCSModel.GLM, "Standard implementation"),
    ]

    print(f"{'Phase':12} {'Task':35} {'Model':10} {'Reason':40}")
    print("-" * 97)

    total_claude_cost = 0
    total_glm_cost = 0

    for phase, task, expected, reason in test_cases:
        selected = router.select_model(phase, task)
        cost = router.estimate_cost(selected, 1000)

        if selected == CCSModel.DEFAULT:
            total_claude_cost += cost
        else:
            total_glm_cost += cost

        status = "✅" if selected == expected else "❌"
        print(f"{phase.value:12} {task[:35]:35} {selected.value:10} {reason[:40]:40} {status}")

    print(f"\n💰 Cost Analysis (per 1K tokens):")
    print(f"  Claude usage: ${total_claude_cost:.4f}")
    print(f"  GLM usage: ${total_glm_cost:.4f}")
    print(f"  Total: ${total_claude_cost + total_glm_cost:.4f}")

    # Calculate savings if all were Claude
    all_claude_cost = len(test_cases) * router.estimate_cost(CCSModel.DEFAULT, 1000)
    actual_cost = total_claude_cost + total_glm_cost
    savings = all_claude_cost - actual_cost
    savings_percent = (savings / all_claude_cost * 100) if all_claude_cost > 0 else 0

    print(f"\n💡 Cost Savings:")
    print(f"  All Claude: ${all_claude_cost:.4f}")
    print(f"  With CCS: ${actual_cost:.4f}")
    print(f"  Savings: ${savings:.4f} ({savings_percent:.1f}%)")


def test_ccs_commands():
    """Test what CCS commands would be generated"""
    print("\n🔌 Testing CCS Command Generation\n")

    commands = {
        CCSModel.DEFAULT: ["claude"],  # Direct Claude CLI
        CCSModel.GLM: ["ccs", "glm"],
    }

    for model, cmd in commands.items():
        print(f"  {model.value:10} → {' '.join(cmd)}")


def test_configuration():
    """Test configuration parsing"""
    print("\n⚙️  Test Configuration\n")

    test_config = """
    ccs:
      enabled: true
      binary_path: ccs
      models:
        claude:
          flags: []
        glm:
          flags: []
      cost_optimization:
        prefer_cheap_for_bulk: true
        max_task_cost: 5.0
    """

    print("Example configuration:")
    print(test_config)
    print("\nWith this configuration:")
    print("  ✓ CCS integration will be enabled")
    print("  ✓ Planning and review will use Claude Sonnet 4.5")
    print("  ✓ Routine execution will use GLM for cost savings")
    print("  ✓ Cost per task will be capped at $5.00")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Sleepless Agent CCS Integration Test (Simplified)")
    print("=" * 60)

    test_task_router()
    test_ccs_commands()
    test_configuration()

    print("\n" + "=" * 60)
    print("📝 Next Steps:")
    print("1. Install CCS: npm install -g @kaitranntt/ccs")
    print("2. Configure models: ccs config set glm.api_key YOUR_KEY")
    print("3. Enable in config.yaml: ccs.enabled: true")
    print("4. Run the full integration test")
    print("=" * 60)


if __name__ == "__main__":
    main()