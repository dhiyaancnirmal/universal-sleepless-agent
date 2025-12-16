# Sleepless Agent with CCS Integration

This is a modified version of [sleepless-agent](https://github.com/context-machine-lab/sleepless-agent) that integrates with [CCS (Claude Code Switch)](https://github.com/kaitranntt/ccs) for intelligent multi-model execution.

## Overview

The CCS integration enables Sleepless Agent to:
- Use **Sonnet 4.5** for high-value planning and review phases
- Use **GLM** for cost-effective execution of routine tasks
- Automatically select the optimal model based on task characteristics
- Track costs and savings across different models

## Architecture

```
Task Input
     ↓
Planning Phase (Sonnet 4.5)
     ↓
Task Decomposition
     ↓
Execution Phase (Intelligent Model Selection)
 ├─ Complex tasks → Sonnet 4.5
 ├─ Routine tasks → GLM
 └─ Large context → Kimi
     ↓
Review Phase (Sonnet 4.5)
     ↓
Result Aggregation
```

## Installation

1. **Prerequisites**:
   ```bash
   # Install Claude Code CLI
   npm install -g @anthropic-ai/claude-code

   # Install CCS
   npm install -g @kaitranntt/ccs
   ```

2. **Setup GLM Profile in CCS**:
   ```bash
   # Configure your GLM API key
   ccs config set glm.api_key "your-glm-api-key"

   # Test the GLM profile
   ccs glm --version
   ```

3. **Install Sleepless Agent**:
   ```bash
   cd sleepless-agent-ccs
   pip install -r requirements.txt
   ```

## Configuration

Update `src/sleepless_agent/config.yaml`:

```yaml
# Enable CCS integration
ccs:
  enabled: true
  binary_path: ccs  # Path to CCS binary

  # Model configurations
  models:
    claude:
      flags: []  # Additional flags for Claude

    glm:
      flags: []  # Additional flags for GLM

    gemini:
      flags: []  # Additional flags for Gemini

    kimi:
      flags: []  # Additional flags for Kimi

  # Cost optimization
  cost_optimization:
    prefer_cheap_for_bulk: true
    max_task_cost: 5.0
    strategy: "auto"  # "auto", "cost_first", "quality_first"
```

## Model Selection Logic

### Planning Phase
- **Always uses Sonnet 4.5** - High-quality reasoning is crucial for good planning

### Execution Phase
The TaskRouter intelligently selects models based on task patterns:

| Task Type | Model | Reason |
|-----------|-------|--------|
| Architecture design | Sonnet 4.5 | Complex reasoning needed |
| Algorithm optimization | Sonnet 4.5 | Performance-critical |
| Security implementation | Sonnet 4.5 | High stakes |
| Feature implementation | GLM | Cost-effective for routine work |
| Test writing | GLM | Well-defined patterns |
| Documentation | GLM | Straightforward generation |
| Large codebase analysis | Kimi | 1M context window |

### Review Phase
- **Always uses Sonnet 4.5** - Quality assurance is critical

## Cost Optimization

### Model Costs (per 1M tokens):
- Sonnet 4.5: ~$15.00
- GLM: ~$0.50
- Kimi: ~$0.25
- Gemini: ~$2.50

### Typical Savings:
- Routine implementation tasks: 95% cost reduction
- Bulk test generation: 97% cost reduction
- Documentation: 98% cost reduction
- Overall average: 70-80% cost savings

## Usage

1. **Start the agent**:
   ```bash
   python -m sleepless_agent.main
   ```

2. **Submit tasks via Slack**:
   ```
   /plan-task Build a REST API for user management
   /execute-task Add comprehensive tests for the API
   /review-task Check security implications
   ```

3. **Monitor model usage**:
   The agent logs model usage statistics:
   ```
   ccs.daily_stats total_cost=2.34 savings=72.5 model_breakdown={'claude': 3, 'glm': 15}
   ```

## Advanced Features

### Custom Model Allocation

You can specify model preferences in task descriptions:

```
# Force Claude for complex task
[CLAUDE] Implement a custom caching layer with LRU eviction

# Use GLM for routine work
[GLM] Add CRUD endpoints for user resource

# Use Kimi for large context
[KIMI] Analyze the entire codebase for security vulnerabilities
```

### Cost Budgeting

Set daily/weekly cost budgets:

```yaml
ccs:
  cost_optimization:
    daily_budget: 10.0  # $10 per day
    weekly_budget: 50.0  # $50 per week

    # What to do when budget is reached
    budget_exceeded_action: "pause"  # "pause" or "warn"
```

## Monitoring

### Model Usage Dashboard

The agent provides detailed usage statistics:

```python
# Get current usage stats
stats = agent.claude.get_model_usage_stats()

# Example output:
{
    "total_cost_usd": 3.45,
    "total_requests": 25,
    "model_breakdown": {
        "claude": {"requests": 5, "cost": 2.25},
        "glm": {"requests": 20, "cost": 1.20}
    },
    "cost_savings": {
        "estimated_claude_only_cost": 15.00,
        "actual_cost": 3.45,
        "savings_usd": 11.55,
        "savings_percent": 77.0
    }
}
```

### Performance Metrics

Track:
- Cost per task type
- Model effectiveness
- Task completion rates by model
- Quality differences between models

## Troubleshooting

### Common Issues

1. **CCS not found**:
   ```bash
   # Ensure CCS is installed and in PATH
   which ccs
   ccs --version
   ```

2. **GLM profile not configured**:
   ```bash
   # Check available profiles
   ccs list

   # Configure GLM
   ccs config set glm.api_key "your-key"
   ```

3. **Model switching not working**:
   - Check logs for `ccs_executor` messages
   - Verify `ccs.enabled: true` in config
   - Ensure all model profiles are configured

### Debug Mode

Enable debug logging:
```yaml
logging:
  level: "DEBUG"
  handlers:
    console:
      enabled: true
```

## Contributing

To extend model support:

1. Add new model to `CCSModel` enum in `ccs_executor.py`
2. Update cost matrix in `TaskRouter`
3. Add model selection patterns in `select_model()`
4. Update configuration schema

## License

Same as original sleepless-agent project.