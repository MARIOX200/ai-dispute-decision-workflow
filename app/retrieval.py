from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .config import settings
from .schemas import RetrievalHit

@dataclass
class Doc:
    source_id: str
    title: str
    text: str

class Retriever:
    def __init__(self, kb_dir: str = "data/knowledge_base"):
        self.docs: list[Doc] = []
        for path in sorted(Path(kb_dir).glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
            self.docs.append(Doc(path.stem, title, text))
        if not self.docs:
            raise RuntimeError("Knowledge base is empty")
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([d.text for d in self.docs])

    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[RetrievalHit]:
        threshold = settings.min_retrieval_score if min_score is None else min_score
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix)[0]
        order = scores.argsort()[::-1][:k]
        hits: list[RetrievalHit] = []
        for i in order:
            score = float(scores[i])
            if score < threshold:
                continue
            d = self.docs[int(i)]
            hits.append(
                RetrievalHit(
                    source_id=d.source_id,
                    title=d.title,
                    score=round(score, 4),
                    excerpt=d.text[:520],
                )
            )
        return hits
