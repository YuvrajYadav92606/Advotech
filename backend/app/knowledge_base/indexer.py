import os
import json
from typing import List, Dict, Optional
from app.schemas.knowledge_base import LegalDocumentItem, KBSearchQuery, KBStatistics

class LegalKnowledgeIndexer:
    """
    In-memory knowledge indexer for Indian Statutes & Landmark Case Laws.
    Maintains clean provenance metadata, tracks statutory amendments,
    and formats data for downstream ML training pipelines.
    """
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Default to adjacent 'data' directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(current_dir, "data")
            
        self.data_dir = data_dir
        self.documents: Dict[str, LegalDocumentItem] = {}
        self.load_corpus()

    def load_corpus(self):
        """
        Loads and validates JSONL statutes and case laws.
        """
        self.documents.clear()
        
        statutes_file = os.path.join(self.data_dir, "statutes.jsonl")
        case_laws_file = os.path.join(self.data_dir, "case_laws.jsonl")
        
        for file_path in (statutes_file, case_laws_file):
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            item = LegalDocumentItem(**record)
                            self.documents[item.id] = item
                        except Exception as e:
                            print(f"[Warning] Failed to parse line {line_num} in {file_path}: {e}")

    def search(self, query: KBSearchQuery) -> List[LegalDocumentItem]:
        """
        Executes a targeted search across statutes and court judgments.
        Matches against title, section, statute name, legal issues, ratio decidendi, and content.
        """
        terms = [t.lower() for t in query.query.split() if len(t) >= 2]
        if not terms:
            return []
            
        matched_items: List[Tuple[float, LegalDocumentItem]] = []
        
        for item in self.documents.values():
            # Filter by doc_type
            if query.doc_type and item.doc_type.upper() != query.doc_type.upper():
                continue
                
            # Filter by court
            if query.court and item.court_or_authority and query.court.lower() not in item.court_or_authority.lower():
                continue
                
            # Filter active legislation only
            if query.active_only and item.is_amended_or_superseded:
                continue
                
            # Calculate relevance score based on match location
            score = 0.0
            
            # Direct section number match (Highest priority)
            if item.section_number and any(t in item.section_number.lower() for t in terms):
                score += 50.0
                
            # Title match
            title_lower = item.title.lower()
            if all(t in title_lower for t in terms):
                score += 30.0
            else:
                score += sum(10.0 for t in terms if t in title_lower)
                
            # Legal issues match
            for issue in item.legal_issues:
                issue_lower = issue.lower()
                score += sum(8.0 for t in terms if t in issue_lower)
                
            # Ratio decidendi match (Binding legal principle)
            if item.ratio_decidendi:
                ratio_lower = item.ratio_decidendi.lower()
                score += sum(5.0 for t in terms if t in ratio_lower)
                
            # Body content match
            content_lower = item.content.lower()
            score += sum(1.5 for t in terms if t in content_lower)
            
            if score > 0:
                matched_items.append((score, item))
                
        # Sort by relevance score descending
        matched_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in matched_items[:query.limit]]

    def get_document_by_id(self, doc_id: str) -> Optional[LegalDocumentItem]:
        return self.documents.get(doc_id)

    def get_statistics(self) -> KBStatistics:
        """
        Returns statistical distribution of the legal knowledge base.
        """
        total = len(self.documents)
        statutes = sum(1 for d in self.documents.values() if d.doc_type == "STATUTE")
        case_laws = sum(1 for d in self.documents.values() if d.doc_type == "CASE_LAW")
        
        courts: Dict[str, int] = {}
        splits: Dict[str, int] = {}
        categories: Dict[str, int] = {}
        
        for d in self.documents.values():
            court = d.court_or_authority or "Unknown"
            courts[court] = courts.get(court, 0) + 1
            
            split = d.training_split or "unassigned"
            splits[split] = splits.get(split, 0) + 1
            
            for issue in d.legal_issues:
                categories[issue] = categories.get(issue, 0) + 1
                
        return KBStatistics(
            total_documents=total,
            total_statutes=statutes,
            total_case_laws=case_laws,
            categories=categories,
            courts=courts,
            training_splits=splits
        )

    def export_training_dataset(self, split: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Exports the indexed legal dataset formatted for ML model training/fine-tuning.
        Can filter by training split ('train', 'validation', 'test').
        """
        records = []
        for doc in self.documents.values():
            if split and doc.training_split != split:
                continue
            records.append({
                "id": doc.id,
                "text": f"{doc.title}\n\n{doc.content}",
                "doc_type": doc.doc_type,
                "statutory_provisions": doc.statutory_provisions,
                "legal_issues": doc.legal_issues,
                "ratio_decidendi": doc.ratio_decidendi,
                "split": doc.training_split
            })
        return records

# Singleton instance
_kb_indexer = None

def get_kb_indexer() -> LegalKnowledgeIndexer:
    global _kb_indexer
    if _kb_indexer is None:
        _kb_indexer = LegalKnowledgeIndexer()
    return _kb_indexer
