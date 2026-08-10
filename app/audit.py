from __future__ import annotations
import json, sqlite3, time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 ts REAL NOT NULL,
 case_id TEXT NOT NULL,
 correlation_id TEXT NOT NULL,
 event_type TEXT NOT NULL,
 payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recommendations (
 case_id TEXT PRIMARY KEY,
 correlation_id TEXT NOT NULL,
 action TEXT NOT NULL,
 confidence REAL NOT NULL,
 payload_json TEXT NOT NULL,
 reviewed INTEGER NOT NULL DEFAULT 0,
 human_action TEXT,
 reviewer TEXT,
 review_comment TEXT,
 reviewed_at REAL,
 status TEXT NOT NULL DEFAULT 'AI_ANALYSED'
);
"""

class AuditStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with sqlite3.connect(self.path) as con:
            con.executescript(SCHEMA)
            self._migrate(con)

    @staticmethod
    def _migrate(con: sqlite3.Connection) -> None:
        cols={row[1] for row in con.execute("PRAGMA table_info(recommendations)").fetchall()}
        if "reviewed_at" not in cols:
            con.execute("ALTER TABLE recommendations ADD COLUMN reviewed_at REAL")
        if "status" not in cols:
            con.execute("ALTER TABLE recommendations ADD COLUMN status TEXT NOT NULL DEFAULT 'AI_ANALYSED'")

    def event(self, case_id: str, correlation_id: str, event_type: str, payload: dict) -> None:
        with sqlite3.connect(self.path) as con:
            con.execute("INSERT INTO events(ts,case_id,correlation_id,event_type,payload_json) VALUES(?,?,?,?,?)",
                        (time.time(), case_id, correlation_id, event_type, json.dumps(payload, ensure_ascii=False)))

    def save_recommendation(self, case_id: str, correlation_id: str, action: str, confidence: float, payload: dict, status: str) -> None:
        with sqlite3.connect(self.path) as con:
            con.execute("INSERT OR REPLACE INTO recommendations(case_id,correlation_id,action,confidence,payload_json,reviewed,status) VALUES(?,?,?,?,?,0,?)",
                        (case_id, correlation_id, action, confidence, json.dumps(payload, ensure_ascii=False), status))

    def get_recommendation(self, case_id: str) -> dict | None:
        with sqlite3.connect(self.path) as con:
            row = con.execute(
                "SELECT correlation_id,action,confidence,payload_json,reviewed,human_action,reviewer,review_comment,reviewed_at,status FROM recommendations WHERE case_id=?",
                (case_id,),
            ).fetchone()
        if not row: return None
        reviewed=bool(row[4])
        agreement=(row[1] == row[5]) if reviewed and row[5] else None
        review=(
            {
                "reviewed": True,
                "reviewer": row[6],
                "human_action": row[5],
                "ai_action": row[1],
                "agreement": agreement,
                "comment": row[7] or "",
                "reviewed_at": row[8],
            }
            if reviewed else {"reviewed": False}
        )
        return {
            "case_id": case_id,
            "correlation_id": row[0],
            "status": row[9],
            "action": row[1],
            "confidence": row[2],
            "payload": json.loads(row[3]),
            "review": review,
        }

    def review(self, case_id: str, human_action: str, reviewer: str, comment: str) -> float:
        reviewed_at=time.time()
        with sqlite3.connect(self.path) as con:
            con.execute(
                "UPDATE recommendations SET reviewed=1,human_action=?,reviewer=?,review_comment=?,reviewed_at=?,status='HUMAN_REVIEWED' WHERE case_id=?",
                (human_action, reviewer, comment, reviewed_at, case_id),
            )
        return reviewed_at
