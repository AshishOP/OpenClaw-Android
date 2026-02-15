
import sqlite3
import json
import os
import math
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Simple cosine similarity without numpy (to keep dependencies minimal on Termux if needed)
# But we can assume numpy is available usually. Let's use pure python for maximum portability first.
def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class LocalSupabaseClient:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._cursor = self._conn.cursor()
        self._init_db()

    def _init_db(self):
        # Create tables closely matching Supabase schema
        # We store embeddings as JSON blobs or BLOBs
        
        # Sessions
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                session_number INTEGER,
                title TEXT,
                content TEXT,
                embedding TEXT,
                file_path TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Case Studies
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_studies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE,
                title TEXT,
                content TEXT,
                embedding TEXT,
                file_path TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                code TEXT 
            )
        """)

        # Protocols
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS protocols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol_id TEXT UNIQUE,
                title TEXT,
                content TEXT,
                embedding TEXT,
                file_path TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                code TEXT
            )
        """)

        # Capabilities
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                content TEXT,
                embedding TEXT,
                file_path TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # System Docs
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                doc_type TEXT,
                content TEXT,
                embedding TEXT,
                file_path TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Memory Bank (mapped to system_docs mostly, but let's keep it handled dynamically)
        
        self._conn.commit()

    def table(self, table_name: str):
        return TableBuilder(self, table_name)

    def rpc(self, func_name: str, params: Dict[str, Any]):
        return RpcBuilder(self, func_name, params)
    
    def upsert(self, table_name: str, data: Dict[str, Any], on_conflict: str = None):
        # Handle upsert logic
        # SQLite >= 3.24 supports UPSERT. Termux usually has modern sqlite.
        # But for compatibility, let's use INSERT OR REPLACE if appropriate, or check existence.
        
        # "data" is a dictionary.
        # "embedding" should be serialized to JSON if present.
        row = data.copy()
        if 'embedding' in row and isinstance(row['embedding'], list):
            row['embedding'] = json.dumps(row['embedding'])
            
        columns = list(row.keys())
        placeholders = ', '.join(['?' for _ in columns])
        col_names = ', '.join(columns)
        values = [row[k] for k in columns]

        # Basic INSERT OR REPLACE logic based on the unique constraints we know
        # file_path is usually the unique key we care about in sync.py
        
        conflict_target = on_conflict if on_conflict else 'file_path'
        
        # Check if column exists in table (crude schema evolution handling)
        # For this exercise, we assume schema is static as defined above.
        
        sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
        
        # SQLite upsert syntax
        # ON CONFLICT(target) DO UPDATE SET ...
        
        # Construct SET clause
        update_assignments = [f"{col}=excluded.{col}" for col in columns if col != 'id']
        set_clause = ", ".join(update_assignments)
        
        sql += f" ON CONFLICT({conflict_target}) DO UPDATE SET {set_clause}"
        
        try:
            self._cursor.execute(sql, values)
            self._conn.commit()
            return QueryResult(data=[row], error=None)
        except Exception as e:
            print(f"Local DB Error: {e}")
            return QueryResult(data=None, error=str(e))

    def delete(self, table_name: str):
        return DeleteBuilder(self, table_name)

class QueryResult:
    def __init__(self, data, error=None):
        self.data = data
        self.error = error

    def execute(self):
        if self.error:
            raise Exception(self.error)
        return self

class TableBuilder:
    def __init__(self, client: LocalSupabaseClient, table_name: str):
        self.client = client
        self.table_name = table_name

    def upsert(self, data: Dict[str, Any], on_conflict: str = None):
        return self.client.upsert(self.table_name, data, on_conflict)

    def delete(self):
        return DeleteBuilder(self.client, self.table_name)

class DeleteBuilder:
    def __init__(self, client: LocalSupabaseClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self._eq_filters = {}

    def eq(self, column: str, value: Any):
        self._eq_filters[column] = value
        return self

    def execute(self):
        if not self._eq_filters:
            raise Exception("Delete requires at least one filter (safety)")
        
        conditions = " AND ".join([f"{k}=?" for k in self._eq_filters.keys()])
        values = list(self._eq_filters.values())
        
        sql = f"DELETE FROM {self.table_name} WHERE {conditions}"
        self.client._cursor.execute(sql, values)
        self.client._conn.commit()
        return QueryResult(data=[], error=None)

class RpcBuilder:
    def __init__(self, client: LocalSupabaseClient, func_name: str, params: Dict[str, Any]):
        self.client = client
        self.func_name = func_name
        self.params = params

    def execute(self):
        # Emulate the search RPCs
        # search_sessions(query_embedding, match_threshold, match_count)
        
        query_embedding = self.params.get('query_embedding')
        threshold = self.params.get('match_threshold', 0.3)
        limit = self.params.get('match_count', 5)
        
        # Map RPC name to table
        # search_sessions -> sessions
        # search_case_studies -> case_studies
        # etc.
        
        table_map = {
            "search_sessions": "sessions",
            "search_case_studies": "case_studies",
            "search_protocols": "protocols",
            "search_capabilities": "capabilities",
            "search_system_docs": "system_docs",
            # Add others as needed
        }
        
        target_table = table_map.get(self.func_name)
        if not target_table:
            # Maybe it's a direct table search?
            return QueryResult(data=[], error=f"Unknown RPC {self.func_name}")

        # Fetch all embeddings from the table
        # This is a brute-force scan. Fine for "personal" scale (<10k docs).
        # Optimization: use numpy if available, use specialized lib if huge.
        
        self.client._cursor.execute(f"SELECT * FROM {target_table}")
        columns = [description[0] for description in self.client._cursor.description]
        rows = self.client._cursor.fetchall()
        
        results = []
        
        for row in rows:
            record = dict(zip(columns, row))
            emb_json = record.get('embedding')
            if not emb_json:
                continue
                
            try:
                doc_embedding = json.loads(emb_json)
                sim = cosine_similarity(query_embedding, doc_embedding)
                
                if sim > threshold:
                    # Enrich with similarity
                    record['similarity'] = sim
                    # Remove raw embedding from result to save bandwidth/noise
                    del record['embedding']
                    results.append(record)
            except:
                continue
        
        # Sort by similarity descending
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return QueryResult(data=results[:limit], error=None)

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Athena Local DB CLI")
    parser.add_argument("--db", type=str, default="athena_memory.db", help="Path to SQLite DB")
    subparsers = parser.add_subparsers(dest="command")

    # Search command
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--func", type=str, required=True, help="RPC function name (e.g. search_sessions)")
    search_parser.add_argument("--embedding", type=str, required=True, help="JSON string of embedding vector")
    search_parser.add_argument("--threshold", type=float, default=0.3)
    search_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    if args.command == "search":
        client = LocalSupabaseClient(args.db)
        emb = json.loads(args.embedding)
        res = client.rpc(args.func, {
            "query_embedding": emb,
            "match_threshold": args.threshold,
            "match_count": args.limit
        }).execute()
        
        print(json.dumps(res.data))
    else:
        parser.print_help()
