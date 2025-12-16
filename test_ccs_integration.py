#!/usr/bin/env python3
"""Test script for CCS integration with sleepless-agent"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sleepless_agent.core.ccs_executor import CCSAwareExecutor, TaskRouter, CCSModel, ModelPhase
from sleepless_agent.utils.config import get_config


async def test_ccs_integration():
    """Test CCS integration components"""

    print("🔧 Testing CCS Integration for Sleepless Agent\n")

    # Load configuration
    config = get_config()
    ccs_config = getattr(config, 'ccs', {})

    print(f"CCS enabled: {ccs_config.get('enabled', False)}")
    print(f"CCS binary path: {ccs_config.get('binary_path', 'ccs')}")

    # Test Task Router
    print("\n📋 Testing Task Router...")
    router = TaskRouter(ccs_config)

    test_tasks = [
        ("Implement a REST API endpoint", "implementation"),
        ("Design a microservices architecture", "architecture"),
        ("Write unit tests for user service", "testing"),
        ("Add documentation for API", "documentation"),
        ("Optimize database queries", "optimization"),
        ("Review security implementation", "security"),
    ]

    for description, category in test_tasks:
        model = router.select_model(ModelPhase.EXECUTION, description)
        cost = router.estimate_cost(model, 1000)  # Estimate for 1K tokens
        print(f"  {category:20} → {model.value:10} (${cost:.4f}/1K tokens)")

    # Test executor initialization
    print("\n🚀 Testing CCS-Aware Executor...")
    try:
        executor = CCSAwareExecutor(
            workspace_root="./test_workspace",
            enable_ccs=ccs_config.get('enabled', False),
            ccs_config=ccs_config.__dict__ if hasattr(ccs_config, '__dict__') else {},
        )
        print(f"  Executor initialized successfully")
        print(f"  CCS enabled: {executor.enable_ccs}")
        print(f"  Default model: {executor.default_model}")

        # Test model command generation
        print("\n🔌 Testing model command generation...")
        for model in [CCSModel.CLAUDE, CCSModel.GLM, CCSModel.GEMINI, CCSModel.KIMI]:
            cmd = executor._get_cli_command(model)
            print(f"  {model.value:10} → {' '.join(cmd)}")

        # Test model usage tracking
        print("\n📊 Testing model usage tracking...")
        stats = executor.get_model_usage_stats()
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Total cost: ${stats['total_cost_usd']:.4f}")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("\n⚠️  Note: This is expected if CCS is not installed or configured")

    print("\n✅ CCS integration test completed!")


async def test_simple_task():
    """Test a simple task execution with CCS"""

    print("\n🎯 Testing simple task execution...")

    try:
        # Load configuration
        config = get_config()
        ccs_config = getattr(config, 'ccs', {})

        # Create executor
        executor = CCSAwareExecutor(
            workspace_root="./test_workspace",
            enable_ccs=ccs_config.get('enabled', False),
            ccs_config=ccs_config.__dict__ if hasattr(ccs_config, '__dict__') else {},
        )

        # Create a test workspace
        test_workspace = Path("./test_workspace/test_task")
        test_workspace.mkdir(parents=True, exist_ok=True)

        # Simple test task
        task_description = "Create a simple Python function that calculates factorial"

        # Test model selection
        model = executor.task_router.select_model(ModelPhase.EXECUTION, task_description)
        print(f"  Selected model: {model.value}")

        # Note: We won't actually run the task to avoid API costs
        print("  Skipping actual execution (to avoid API costs)")

        # Cleanup
        import shutil
        shutil.rmtree(test_workspace, ignore_errors=True)

    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Sleepless Agent CCS Integration Test")
    print("=" * 60)

    asyncio.run(test_ccs_integration())
    asyncio.run(test_simple_task())

    print("\n📝 To use CCS integration:")
    print("  1. Install CCS: npm install -g @kaitranntt/ccs")
    print("  2. Configure GLM: ccs config set glm.api_key YOUR_KEY")
    print("  3. Enable in config.yaml: ccs.enabled: true")
    print("  4. Run: python -m sleepless_agent.main")


if __name__ == "__main__":
    main()