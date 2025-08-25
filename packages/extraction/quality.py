"""
Quality scoring for extracted facts
"""

import re
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

from .extractors import ExtractedFact

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for an extracted fact"""
    confidence_score: float
    source_reliability: float
    extraction_consistency: float
    context_relevance: float
    overall_quality: float

class QualityScorer:
    """Scores the quality of extracted facts"""
    
    def __init__(self):
        self.trusted_domains = self._load_trusted_domains()
        self.quality_indicators = self._load_quality_indicators()
    
    def _load_trusted_domains(self) -> Dict[str, float]:
        """Load trusted domain reliability scores"""
        return {
            "tesla.com": 0.95,
            "nrel.gov": 0.9,
            "eia.gov": 0.9,
            "irena.org": 0.85,
            "energy.gov": 0.9,
            "doe.gov": 0.9,
            "iea.org": 0.85,
            "lazard.com": 0.8,
            "bloomberg.com": 0.75,
            "greentechmedia.com": 0.7,
            "pv-magazine.com": 0.7,
            "energystorage.news": 0.65,
        }
    
    def _load_quality_indicators(self) -> Dict[str, Dict[str, float]]:
        """Load quality indicators for different contexts"""
        return {
            "high_quality_phrases": {
                "official specification": 0.2,
                "technical datasheet": 0.15,
                "manufacturer specification": 0.15,
                "certified performance": 0.1,
                "laboratory tested": 0.1,
                "independently verified": 0.1,
                "according to": 0.05,
                "as per": 0.05,
            },
            "low_quality_phrases": {
                "approximately": -0.1,
                "around": -0.1,
                "roughly": -0.1,
                "estimated": -0.15,
                "rumored": -0.3,
                "allegedly": -0.3,
                "unconfirmed": -0.3,
                "speculation": -0.4,
            },
            "context_indicators": {
                "table": 0.1,
                "specification": 0.1,
                "datasheet": 0.15,
                "manual": 0.1,
                "documentation": 0.05,
                "press release": -0.05,
                "blog": -0.1,
                "forum": -0.2,
            }
        }
    
    def score_fact(self, fact: ExtractedFact, source_url: str = "", 
                   document_context: Dict[str, Any] = None) -> QualityMetrics:
        """Score the quality of an extracted fact"""
        try:
            # Base confidence from extraction method
            confidence_score = fact.confidence
            
            # Source reliability score
            source_reliability = self._score_source_reliability(source_url)
            
            # Context relevance score
            context_relevance = self._score_context_relevance(
                fact.span_excerpt, document_context or {}
            )
            
            # Extraction consistency (placeholder - would compare with other extractions)
            extraction_consistency = 0.8  # Default value
            
            # Calculate overall quality score
            overall_quality = self._calculate_overall_quality(
                confidence_score, source_reliability, 
                extraction_consistency, context_relevance
            )
            
            return QualityMetrics(
                confidence_score=confidence_score,
                source_reliability=source_reliability,
                extraction_consistency=extraction_consistency,
                context_relevance=context_relevance,
                overall_quality=overall_quality
            )
            
        except Exception as e:
            logger.error(f"Error scoring fact quality: {e}")
            return QualityMetrics(0.5, 0.5, 0.5, 0.5, 0.5)
    
    def _score_source_reliability(self, source_url: str) -> float:
        """Score source reliability based on domain"""
        if not source_url:
            return 0.5  # Default for unknown source
        
        try:
            from urllib.parse import urlparse
            domain = urlparse(source_url).netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check trusted domains
            for trusted_domain, score in self.trusted_domains.items():
                if domain == trusted_domain or domain.endswith('.' + trusted_domain):
                    return score
            
            # Default score for unknown domains
            return 0.6
            
        except Exception as e:
            logger.warning(f"Error parsing source URL {source_url}: {e}")
            return 0.5
    
    def _score_context_relevance(self, span_excerpt: str, 
                                document_context: Dict[str, Any]) -> float:
        """Score context relevance of the extracted fact"""
        try:
            base_score = 0.7
            
            # Check for quality indicators in the span
            span_lower = span_excerpt.lower()
            
            # High quality phrases
            for phrase, boost in self.quality_indicators["high_quality_phrases"].items():
                if phrase in span_lower:
                    base_score += boost
            
            # Low quality phrases
            for phrase, penalty in self.quality_indicators["low_quality_phrases"].items():
                if phrase in span_lower:
                    base_score += penalty  # penalty is negative
            
            # Context indicators from document
            title = document_context.get("title", "").lower()
            for indicator, boost in self.quality_indicators["context_indicators"].items():
                if indicator in title or indicator in span_lower:
                    base_score += boost
            
            # Check if fact appears in structured data (tables)
            tables = document_context.get("tables", [])
            if self._fact_in_tables(span_excerpt, tables):
                base_score += 0.15
            
            # Ensure score is within bounds
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(f"Error scoring context relevance: {e}")
            return 0.7
    
    def _fact_in_tables(self, span_excerpt: str, tables: List[Dict]) -> bool:
        """Check if the fact appears in structured table data"""
        try:
            # Extract numbers from span
            numbers = re.findall(r'\d+\.?\d*', span_excerpt)
            if not numbers:
                return False
            
            # Check if any of these numbers appear in tables
            for table in tables:
                for row in table.get("rows", []):
                    if isinstance(row, dict):
                        row_text = " ".join(str(v) for v in row.values())
                    elif isinstance(row, list):
                        row_text = " ".join(str(v) for v in row)
                    else:
                        continue
                    
                    for number in numbers:
                        if number in row_text:
                            return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking fact in tables: {e}")
            return False
    
    def _calculate_overall_quality(self, confidence: float, reliability: float,
                                 consistency: float, relevance: float) -> float:
        """Calculate weighted overall quality score"""
        try:
            # Weighted average with emphasis on confidence and reliability
            weights = {
                "confidence": 0.4,
                "reliability": 0.3,
                "consistency": 0.15,
                "relevance": 0.15
            }
            
            overall = (
                confidence * weights["confidence"] +
                reliability * weights["reliability"] +
                consistency * weights["consistency"] +
                relevance * weights["relevance"]
            )
            
            return max(0.0, min(1.0, overall))
            
        except Exception as e:
            logger.error(f"Error calculating overall quality: {e}")
            return 0.5
    
    def filter_facts_by_quality(self, facts: List[ExtractedFact], 
                               min_quality: float = 0.6) -> List[ExtractedFact]:
        """Filter facts by minimum quality threshold"""
        try:
            filtered_facts = []
            
            for fact in facts:
                # Score the fact (simplified - would need full context in real implementation)
                quality = self.score_fact(fact)
                
                if quality.overall_quality >= min_quality:
                    filtered_facts.append(fact)
                else:
                    logger.debug(f"Filtered out low quality fact: {fact.metric} = {fact.value} (quality: {quality.overall_quality:.2f})")
            
            return filtered_facts
            
        except Exception as e:
            logger.error(f"Error filtering facts by quality: {e}")
            return facts  # Return original facts if filtering fails
