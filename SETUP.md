# Sleepless Agent CCS Integration - Setup Guide

## Current Status ✅

You have successfully integrated CCS with Sleepless Agent! Here's what's configured:

- **Claude Code Pro**: Direct access for planning and review phases
- **GLM**: Through CCS for cost-effective execution
- **Intelligent routing**: Tasks automatically use the best model

## Quick Start

1. **Verify CCS is working**:
   ```bash
   ccs --version
   # Should show: CCS (Claude Code Switch) v5.14.0
   ```

2. **Test GLM access**:
   ```bash
   ccs glm "Say hello"
   # Should respond with GLM
   ```

3. **Run the test**:
   ```bash
   python test_ccs_simple.py
   # Shows model selection logic working
   ```

## Configuration

Your `src/sleepless_agent/config.yaml` is already set up:

```yaml
ccs:
  enabled: true
  binary_path: ccs

  models:
    default:
      use_direct_claude: true  # Uses your Claude Pro account
    glm:
      # Already configured with your API key
```

## How It Works

### Model Selection Logic

| Phase | Model | When Used |
|-------|-------|-----------|
| **Planning** | Claude Pro | Always (high-value reasoning) |
| **Review** | Claude Pro | Always (quality assurance) |
| **Execution** | Claude Pro | Complex tasks (architecture, security, optimization) |
| **Execution** | GLM | Routine tasks (implementation, tests, documentation) |

### Cost Savings

- **Claude Pro**: $15/1M tokens (planning/review/complex)
- **GLM**: $0.50/1M tokens (routine execution)
- **Typical savings**: 70-95% on implementation tasks

## Running Sleepless Agent

1. **Start the daemon**:
   ```bash
   cd sleepless-agent-ccs
   python -m sleepless_agent.main
   ```

2. **Monitor logs**:
   ```bash
   tail -f logs/sleepless-agent.log | grep ccs
   ```

3. **Check model usage**:
   The daemon will log daily statistics:
   ```
   ccs.daily_stats total_cost=2.34 savings=75.2 model_breakdown={'default': 5, 'glm': 20}
   ```

## Example Task Flow

When you submit a task like "Build a REST API for user management":

1. **Planning Phase** (Claude Pro):
   - Analyzes requirements
   - Creates structured TODO list
   - Estimates complexity

2. **Execution Phase** (Smart Selection):
   - API endpoints → GLM (routine)
   - Security implementation → Claude Pro (critical)
   - Database schema → GLM (standard)
   - Authentication → Claude Pro (security)

3. **Review Phase** (Claude Pro):
   - Quality check
   - Security review
   - Performance assessment

## Troubleshooting

### GLM Not Working
```bash
# Check GLM profile
ccs glm --version

# If not working, reconfigure:
ccs config set glm.api_key "your-api-key"
```

### Claude Direct Access Issues
```bash
# Verify Claude CLI
claude --version

# Check usage
claude /usage
```

### Force Claude for a Task
Add to your task description:
```
[CLAUDE] Implement the critical security module
```

## Performance Tips

1. **Batch similar tasks**: GLM is great for repetitive work
2. **Use GLM for**: CRUD operations, tests, documentation, migrations
3. **Use Claude for**: Architecture, security, performance optimization, complex debugging

## Monitoring

To see real-time model usage:
```bash
# In the sleepless-agent logs:
grep "ccs_executor" logs/sleepless-agent.log
```

This shows:
- Which model was selected
- Why it was selected
- Cost tracking

## Cost Optimization

The system automatically:
- Routes routine tasks to GLM
- Uses Claude only when necessary
- Tracks and reports savings

Expected monthly costs with moderate usage:
- Planning (Claude): ~$10-20
- Execution (mostly GLM): ~$5-10
- Review (Claude): ~$10-15
- **Total**: ~$25-45 (vs $150+ with Claude-only)

## Success! 🎉

You now have a hybrid AI system that:
- Maximizes your Claude Pro value
- Leverages cost-effective GLM for bulk work
- Automatically optimizes for both quality and cost
- Runs 24/7 with intelligent resource allocation