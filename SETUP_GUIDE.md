# Quick Setup Guide for Universal Sleepless Agent

## Prerequisites Already Done ✅
- Python 3.11+ installed
- CCS installed and GLM configured
- Claude Code CLI installed
- Dependencies installed

## Step 1: Configure Slack Bot

### Create Slack App
1. Go to: https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: `Sleepless Agent`
4. Workspace: Your personal/workspace

### Add Permissions
In your Slack app settings:
1. Go to "OAuth & Permissions" → "Bot Token Scopes"
2. Add these scopes:
   - `app_mentions:read`
   - `chat:write`
   - `channels:read`
   - `groups:read`
   - `im:read`
   - `im:write`

### Enable Socket Mode
1. Go to "Socket Mode"
2. Toggle "Enable Socket Mode" ON
3. Click "Generate" under "App-Level Tokens"
4. Give it a name like `socket-token`
5. Copy the token (starts with `xapp-`)

### Subscribe to Events
1. Go to "Event Subscriptions"
2. Toggle "Enable Events" ON
3. Under "Subscribe to bot events", add:
   - `app_mention`
   - `message.channels`

### Install App
1. Go to "Install App"
2. Click "Install to Workspace"
3. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

## Step 2: Update Configuration

### Update .env file
```bash
# Edit .env and replace with your actual tokens:
SLACK_BOT_TOKEN=xoxb-your-actual-token-here
SLACK_APP_TOKEN=xapp-your-actual-token-here
```

### Optional: Update Git Settings
If you want to commit to a repository, update `src/sleepless_agent/config.yaml`:
```yaml
git:
  use_remote_repo: true
  remote_repo_url: git@github.com:dhiyaancnirmal/universal-sleepless-agent.git
  auto_create_repo: true
```

## Step 3: Run Sleepless Agent

### Start the daemon
```bash
cd /Users/dhiyaan/Code/sleepless-agent-ccs
python -m sleepless_agent.main
```

You should see output like:
```
2025-01-XX | INFO | Sleepless Agent starting...
2025-01-XX | INFO | Slack bot connected
2025-01-XX | INFO | AgentOS ready
```

## Step 4: Submit Your First Task

### In Slack
1. Invite the bot to a channel (`/invite @Sleepless Agent`)
2. Submit your task:
   ```
   @Sleepless Agent Implement universal AI editor support for OpenCode and other open-source AI editors
   ```

### Alternative: CLI Task Creation
You can also create tasks via CLI:
```bash
python -m sleepless_agent think "Implement universal AI editor support"
```

## Step 5: Monitor Progress

### Check status
```bash
python -m sleepless_agent check
```

### View results
Results are stored in `./workspace/data/results/`

## Troubleshooting

### Bot not responding?
- Check that Socket Mode is enabled
- Verify both tokens are correct
- Make sure bot is invited to the channel

### Tasks not executing?
- Check Claude CLI: `claude --version`
- Check GLM: `ccs glm "test"`
- Check logs in `./workspace/logs/`

### Need to stop the daemon?
Press `Ctrl+C` in the terminal

## Pro Tips

1. **Run in background**: Use `nohup` or `screen`
   ```bash
   nohup python -m sleepless_agent.main > agent.log 2>&1 &
   ```

2. **Custom commands**: Create Slack shortcuts for common tasks

3. **Cost monitoring**: The system tracks usage and costs automatically

4. **Git integration**: Enable to automatically commit work

## Next Steps

Once your first task is running, you can:
- Submit multiple tasks
- Create projects with `-p` flag
- Generate automatic tasks
- Monitor through the dashboard (if enabled)

Happy coding with your 24/7 AI assistant! 🚀