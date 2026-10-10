# EAGv2 Session 12: Agentic Query Assistant

A Python command-line agent that interprets requests, plans tool calls, executes them through Model Context Protocol (MCP) servers, evaluates results, and produces a final summary. It supports visible browser automation, local document search, PDF conversion, image captioning, and saved session memory.

The application runs on your computer. Gemini provides reasoning through its API; Playwright launches the browser locally in a visible desktop window.

## Requirements

- Python 3.11 or newer; `.python-version` selects 3.11.
- `uv` installed and available in your terminal.
- A Gemini API key and access to a text-generation model.
- Chromium installed through Playwright and a logged-in graphical desktop session.
- Ollama for document indexing, retrieval, and image captioning.

Run all commands below from the repository root. Examples use Windows PowerShell.

## Setup

### 1. Install dependencies and Chromium

```powershell
uv sync
uv run playwright install chromium
```

Dependencies are declared in `pyproject.toml` and resolved in `uv.lock`.

### 2. Configure Gemini

Create `.env` in the repository root:

```dotenv
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=your_available_gemini_model_id
```

Use a model ID available to your account. If `GEMINI_MODEL` is omitted, the agent uses `config/models.json` and its model-not-found fallbacks. The configured names may need updating for your account. `.env` is ignored by Git.

`config/profiles.yaml` selects the provider:

```yaml
llm:
  text_generation: gemini
  embedding: nomic
```

The model manager also supports the Ollama entries in `config/models.json`. The current summarizer still requires `GEMINI_API_KEY` at initialization, even if an Ollama text model is selected.

### 3. Set the document server path

Edit `config/mcp_server_config.yaml`: set the document server's `cwd` to the absolute path of your `mcp_servers` directory. The checked-in path points to the original Windows checkout.

```yaml
mcp_servers:
  - id: documents
    script: mcp_server_2.py
    cwd: C:/path/to/EAGv2_assignment_S12/mcp_servers
    description: Local document search and extraction
  - id: webbrowsing
    script: http://localhost:8100/sse
    transport: sse
    description: Visible local browser automation
```

The document server uses stdio and starts automatically through `main.py`. The browser server uses SSE and must be started separately.

### 4. Prepare document and image tools

Install Ollama, start its desktop service, and download these models:

```powershell
ollama pull nomic-embed-text
ollama pull phi4
ollama pull gemma3:12b
```

If the Ollama service is not already running, start it in another terminal:

```powershell
ollama serve
```

The document server connects to `http://localhost:11434`. It uses `nomic-embed-text` for embeddings, `phi4:latest` for semantic segmentation, and `gemma3:12b` for image captions. These names are defined in `mcp_servers/mcp_server_2.py`, independently of the agent model settings.

Place input documents in `mcp_servers/documents/`. The document server processes that folder on startup and saves its retrieval index in `mcp_servers/faiss_index/`. Restart the document server by restarting `main.py` after adding documents. A search also attempts indexing if the index is missing.

For browser-only use, you can omit the documents entry from your MCP configuration and skip Ollama.

Optional: install the spaCy model for better named-entity extraction in session memory:

```powershell
uv run python -m spacy download en_core_web_sm
```

Without it, the agent uses a blank English model and prints an informational message.

## How to run

### Terminal 1: start BrowserMCP

```powershell
uv run python browserMCP/browser_mcp_sse.py
```

Wait for:

```text
Uvicorn running on http://127.0.0.1:8100
```

Keep this terminal running. Browser tools launch a visible window because `browserMCP/mcp_utils/utils.py` sets `headless=False`. The window opens on the first browser tool call, rather than when the server starts.

### Terminal 2: start the agent

```powershell
uv run main.py
```

The agent lists discovered MCP tools, then displays the `You:` prompt. Enter a request. After the final summary, press Enter to continue or type `exit`. At the main prompt, either `exit` or `quit` ends the application.

Stop BrowserMCP with Ctrl+C in Terminal 1. After changing browser code, restart both BrowserMCP and `main.py`: restarting the agent alone does not reload the separate browser server. Restart `main.py` after changing model settings.

## Basic example

Enter:

```text
Open https://www.inkers.ai in a new browser tab and tell me the main heading.
```

The normal execution flow is:

1. **Perception** identifies the website and requested result, with relevant saved memory when available.
2. **Decision** creates a plan and generates code that calls discovered MCP tools.
3. **Execution** invokes tools such as `open_tab` or `go_to_url`. Playwright opens the local browser and returns page state and interactive element IDs.
4. **Perception** evaluates the returned results and decides whether more steps are needed.
5. **Summarization** reports the outcome and saves a JSON session log.

The exact plan depends on the model. A successful run opens the website and reports its observed heading. For failures, inspect the returned tool result: a code variant can finish executing while a tool returns an error string.

Other requests to try:

```text
Open https://www.inkers.ai and summarize the products described on its homepage.
```

```text
Search the stored documents for the invoice total and show the relevant extract.
```

The document example requires appropriate files in `mcp_servers/documents/` and the Ollama models above.

To check browser automation directly without running the reasoning loop, keep BrowserMCP running and execute:

```powershell
uv run python browserMCP/verify_visible_browser.py
```

This calls the server on port 8100, navigates to `https://www.inkers.ai/`, and prints the tool result.

## Project layout

| Path | Purpose |
| --- | --- |
| `main.py` | Interactive entry point and MCP discovery |
| `agent/` | Agent loop, model manager, context, and sessions |
| `perception/` | Request interpretation and result evaluation |
| `decision/` | Plans and executable tool-call variants |
| `action/` | Code execution and saved step state |
| `summarization/` | Final responses |
| `browserMCP/` | Browser tools, Playwright session, and SSE server |
| `mcp_servers/` | MCP dispatcher and document tools |
| `memory/` | Session logs, summary indexing, and memory search |
| `prompts/` | Perception, decision, and summarizer instructions |
| `config/` | Model, agent profile, and MCP settings |

Generated outputs are ignored by Git:

- `memory/session_logs/YYYY/MM/DD/`: JSON session logs.
- `memory/session_summaries_index/`: searchable session summaries.
- `action/sandbox_state/`: saved execution state.
- `mcp_servers/faiss_index/`: document retrieval index.
- `dom_dumps/`, `media/screenshots/`, and `media/pdf/`: browser artifacts.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Browser tools missing or connection to port 8100 fails | Start BrowserMCP first, confirm its listening message, then restart `main.py`. |
| `unexpected keyword argument 'devtools'` | Use the current profile code, which excludes this argument, and restart BrowserMCP to reload it. |
| `Target page, context or browser has been closed` | The handle is no longer valid. The current server discards closed sessions and initializes a fresh one on the next request. Restart BrowserMCP if it persists. |
| No visible browser | Call a browser tool, check `headless=False`, and run the server in your logged-in desktop session. |
| Chromium executable missing | Run `uv run playwright install chromium`. |
| Document server startup failure | Correct its absolute `cwd` in `config/mcp_server_config.yaml`. |
| Ollama connection failure | Start Ollama and check installed models with `ollama list`. |
| Missing API key or model-not-found error | Check `.env` and select an available model using `GEMINI_MODEL`. |
| spaCy fallback message | Optionally install `en_core_web_sm` using the command above. |

The browser runs locally. A generated summary claiming that a cloud environment prevents displaying your browser does not describe this application's architecture; diagnose the concrete tool error instead.
