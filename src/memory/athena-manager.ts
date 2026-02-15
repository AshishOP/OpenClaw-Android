
import { exec } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import type { OpenClawConfig } from "../config/config.js";
import type { 
  MemorySearchManager, 
  MemorySearchResult, 
  MemoryProviderStatus 
} from "./types.js";
import { resolveAgentWorkspaceDir } from "../agents/agent-scope.js";
import { createSubsystemLogger } from "../logging/subsystem.js";

const execAsync = promisify(exec);
const log = createSubsystemLogger("memory:athena");

export class AthenaMemoryManager implements MemorySearchManager {
  private constructor(
    private readonly deps: {
      cfg: OpenClawConfig;
      agentId: string;
      athenaRoot: string;
      dbPath: string;
    }
  ) {}

  static async create(params: {
    cfg: OpenClawConfig;
    agentId: string;
  }): Promise<AthenaMemoryManager> {
    const athenaRoot = path.resolve(process.cwd(), "Athena");
    // In Termux, we'll store the DB in the agent's workspace or a fixed location
    const workspaceDir = resolveAgentWorkspaceDir(params.cfg, params.agentId);
    const dbPath = path.join(workspaceDir, "athena_memory.db");

    return new AthenaMemoryManager({
      ...params,
      athenaRoot,
      dbPath,
    });
  }

  async search(
    query: string,
    opts?: { maxResults?: number; minScore?: number; sessionKey?: string }
  ): Promise<MemorySearchResult[]> {
    // 1. Generate embedding using OpenClaw's internal logic (usually Gemini)
    // For now, let's assume we need to call it. 
    // Actually, OpenClaw has embedding logic in src/memory/manager.js or similar.
    
    // To keep it simple and robust, we'll use a placeholder or call Athena's embedding python if needed.
    // However, Athena expects the embedding to be passed in.
    
    // Let's see if we can get an embedding from OpenClaw.
    const embedding = await this.getEmbedding(query);
    if (!embedding) return [];

    const results: MemorySearchResult[] = [];
    
    // We search across multiple tables (sessions, system_docs, etc.)
    const tables = ["search_sessions", "search_system_docs", "search_case_studies"];
    
    for (const func of tables) {
      try {
        const cmd = `python3 ${path.join(this.deps.athenaRoot, "src/athena/memory/local_db.py")} --db ${this.deps.dbPath} search --func ${func} --embedding '${JSON.stringify(embedding)}' --limit ${opts?.maxResults ?? 5} --threshold ${opts?.minScore ?? 0.3}`;
        
        const { stdout } = await execAsync(cmd);
        const data = JSON.parse(stdout);
        
        for (const item of data) {
          results.push({
            path: item.file_path || item.title || "unknown",
            score: item.similarity,
            snippet: item.content,
            startLine: 1,
            endLine: 1, // We don't have line numbers in the simple SQLite table yet
            source: func.includes("session") ? "sessions" : "memory"
          });
        }
      } catch (err) {
        log.warn(`Failed searching table ${func}: ${err}`);
      }
    }

    return results.sort((a, b) => b.score - a.score).slice(0, opts?.maxResults ?? 10);
  }

  async readFile(params: { relPath: string; from?: number; lines?: number }) {
    // For Athena, we might just return the content from DB if shared, or read from disk
    // Since Athena stores content in DB, we could fetch it.
    // For now, return empty or try to read file if it exists
    return { text: "Content from Athena memory", path: params.relPath };
  }

  status(): MemoryProviderStatus {
    return {
      backend: "athena" as any,
      provider: "athena-local",
      dbPath: this.deps.dbPath,
      vector: { enabled: true, available: true }
    };
  }

  async probeEmbeddingAvailability() {
    return { ok: true };
  }

  async probeVectorAvailability() {
    return true;
  }

  private async getEmbedding(text: string): Promise<number[] | null> {
    // Hook into OpenClaw's embedding logic
    // This is a bit tricky without importing the manager which might cause circular deps
    // But we'll try to use a simple fetch to Gemini if possible.
    
    const apiKey = process.env.GOOGLE_API_KEY;
    if (!apiKey) return null;

    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=${apiKey}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "models/embedding-001",
          content: { parts: [{ text }] }
        })
      });
      const data = await response.json() as any;
      return data.embedding.values;
    } catch (err) {
      log.warn(`Failed to get embedding: ${err}`);
      return null;
    }
  }
}
