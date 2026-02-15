# Architectural Standard: Sovereign Gateway (The Sidecar Pattern)

> **Source**: "Stolen" from OpenClaw (Moltbot) Architecture (2026-01-31).
> **Status**: REFERENCE (Future Roadmap for `sidecar.py`)
> **Purpose**: Decouple the "Brain" (LLM/Context) from the "Hands" (Device Execution) via a persistent control plane.

---

## 1. The Core Problem

Current "Agent" implementations (like `sidecar.py`) are often monolithic scripts running in a terminal.
**Limitation**: If the terminal closes, the agent dies. If the machine sleeps, the agent sleeps. It cannot reach "across" devices (e.g., control Mac from Phone).

## 2. The Solution: Gateway Architecture

The "Sovereign Gateway" pattern splits the agent into three distinct layers:

### Layer 1: The Gateway (Control Plane)

- **Role**: The "Brain Stem".
- **Tech**: Long-running WebSocket Server (Node/Python).
- **Responsibility**:
  - Maintains state (Sessions, Queue).
  - Routes messages (Unified Inbox).
  - Manages Auth (Tailscale/SSH).
- **Location**: Runs on a continuously available host (Mac Mini, Linux VPS).

### Layer 2: The Nodes (Device Hands)

- **Role**: The "Effectors".
- **Tech**: Lightweight binaries/apps on target devices.
- **Responsibility**:
  - `system.run`: Execute local shell commands.
  - `screen.record` / `camera.snap`: Sensory I/O.
  - `notify`: Native OS notifications.
- **Behavior**: Connect *outbound* to the Gateway via WebSocket.

### Layer 3: The Interfaces (Channels)

- **Role**: The "input".
- **Tech**: API Adapters.
- **Targets**: WhatsApp, Telegram, Slack, Discord, iMessage.
- **Pattern**: The Gateway treats all channels as a single `Universal Inbox`.

---

## 3. Key stolen Patterns

### A. The "Universal Inbox" Abstraction

Don't write a "Telegram Bot" and a "Slack Bot".
Write a **Gateway** that accepts `Message` objects and routes them to an `Agent`.
The Agent replies with text, which the Gateway routes back to the correct `Channel`.

### B. "Node" Mode (Remote Execution)

Instead of the Agent trying to SSH into a server to run a command, the Server runs a **Node** that connects to the Agent.

- **Inversion of Control**: The target device *asks* for work. This bypasses firewalls (NAT traversal via WebSocket).

### C. Tailscale as Identity

Authentication is hard. "Stolen" pattern:

- Use **Tailscale Serve** (or Funnel) to expose the Gateway.
- Use Tailscale Identity Headers for Auth.
- Zero password management.

---

## 4. Athena Integration Roadmap

Crucial evolution path for `sidecar.py`:

1. **Phase 1 (Current)**: Monolithic Script. (Fragile).
2. **Phase 2 (Gateway)**: Split `sidecar.py` into `server.py` (Gateway) and `worker.py` (Node).
3. **Phase 3 (Universal)**: Implement the "Universal Inbox" to unify Telegram/obsidian-notes inputs.

---

## Tagging

# protocol #architecture #gateway #sidecar #stolen
