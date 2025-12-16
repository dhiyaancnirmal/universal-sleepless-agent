# First Task for Universal Sleepless Agent

## Task: Implement Universal AI Editor Support

### Current State
- Sleepless Agent only supports Claude Code directly and CCS for model switching
- Need to extend support to other open-source AI editors and CLI tools

### Required Implementation

1. **Research Phase** (Claude)
   - Investigate popular open-source AI editors:
     - OpenCode
     - CodeLlama (local)
     - StarCoder
     - Aider (CLI)
     - Continue.dev
     - Codeium CLI
   - Document their CLI interfaces and capabilities

2. **Design Phase** (Claude)
   - Create abstract `AIEditor` interface
   - Design plugin architecture for multiple editors
   - Plan cost optimization strategies

3. **Implementation** (GLM - routine work)
   - Create `ai_editor_factory.py`
   - Implement OpenCode integration
   - Add CodeLlama local support via Ollama
   - Create configuration for multiple editors

4. **Testing** (GLM)
   - Write tests for each editor integration
   - Create switching validation

### Expected Outcome
- Sleepless Agent can work with any AI editor
- Intelligent cost optimization across free/paid models
- Plugin system for adding new editors

### Task Priority
- SERIOUS (this is core functionality)

### Slack Command
```
[SERIOUS] Implement universal AI editor support for Sleepless Agent to work with OpenCode, CodeLlama, and other open-source AI coding assistants
```