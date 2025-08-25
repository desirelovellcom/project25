"""
Fact extraction from parsed documents using rules and LLM
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class ExtractedFact:
    """Represents an extracted fact with metadata"""
    metric: str
    value: float
    unit: str
    span_excerpt: str
    confidence: float
    source_section: str = ""
    extraction_method: str = ""

class FactExtractor(ABC):
    """Abstract base class for fact extractors"""
    
    @abstractmethod
    def extract_facts(self, parsed_doc: Dict[str, Any]) -> List[ExtractedFact]:
        """Extract facts from parsed document"""
        pass

class RuleBasedExtractor(FactExtractor):
    """Rule-based fact extractor using regex patterns"""
    
    def __init__(self):
        self.patterns = self._load_extraction_patterns()
    
    def _load_extraction_patterns(self) -> Dict[str, List[Dict]]:
        """Load extraction patterns for different metrics"""
        return {
            "capacity_kwh": [
                {
                    "pattern": r"(\d+\.?\d*)\s*kWh\s*(?:usable\s*)?capacity",
                    "unit": "kWh",
                    "confidence": 0.9
                },
                {
                    "pattern": r"capacity[:\s]*(\d+\.?\d*)\s*kWh",
                    "unit": "kWh", 
                    "confidence": 0.8
                },
                {
                    "pattern": r"(\d+\.?\d*)\s*kilowatt.?hours?\s*(?:of\s*)?(?:usable\s*)?(?:capacity|storage)",
                    "unit": "kWh",
                    "confidence": 0.85
                }
            ],
            "power_kw": [
                {
                    "pattern": r"(\d+\.?\d*)\s*kW\s*(?:continuous\s*)?power",
                    "unit": "kW",
                    "confidence": 0.9
                },
                {
                    "pattern": r"power\s*(?:rating|output)[:\s]*(\d+\.?\d*)\s*kW",
                    "unit": "kW",
                    "confidence": 0.85
                },
                {
                    "pattern": r"(\d+\.?\d*)\s*kilowatts?\s*(?:of\s*)?(?:power|output)",
                    "unit": "kW",
                    "confidence": 0.8
                }
            ],
            "efficiency_percent": [
                {
                    "pattern": r"(\d+\.?\d*)%\s*(?:round.?trip\s*)?efficiency",
                    "unit": "%",
                    "confidence": 0.9
                },
                {
                    "pattern": r"efficiency[:\s]*(\d+\.?\d*)%",
                    "unit": "%",
                    "confidence": 0.85
                },
                {
                    "pattern": r"(\d+\.?\d*)\s*percent\s*efficient",
                    "unit": "%",
                    "confidence": 0.8
                }
            ],
            "warranty_years": [
                {
                    "pattern": r"(\d+).?year\s*(?:product\s*)?warranty",
                    "unit": "years",
                    "confidence": 0.9
                },
                {
                    "pattern": r"warranty[:\s]*(\d+)\s*years?",
                    "unit": "years",
                    "confidence": 0.85
                },
                {
                    "pattern": r"guaranteed\s*for\s*(\d+)\s*years?",
                    "unit": "years",
                    "confidence": 0.8
                }
            ],
            "cycle_life": [
                {
                    "pattern": r"(\d+,?\d*)\s*(?:charge\s*)?cycles?",
                    "unit": "cycles",
                    "confidence": 0.85
                },
                {
                    "pattern": r"cycle\s*life[:\s]*(\d+,?\d*)",
                    "unit": "cycles",
                    "confidence": 0.9
                },
                {
                    "pattern": r"up\s*to\s*(\d+,?\d*)\s*cycles?",
                    "unit": "cycles",
                    "confidence": 0.8
                }
            ],
            "price_usd": [
                {
                    "pattern": r"\$(\d+,?\d*)\s*(?:USD|dollars?)?",
                    "unit": "USD",
                    "confidence": 0.7
                },
                {
                    "pattern": r"price[:\s]*\$(\d+,?\d*)",
                    "unit": "USD",
                    "confidence": 0.8
                },
                {
                    "pattern": r"(\d+,?\d*)\s*USD",
                    "unit": "USD",
                    "confidence": 0.75
                }
            ]
        }
    
    def extract_facts(self, parsed_doc: Dict[str, Any]) -> List[ExtractedFact]:
        """Extract facts using rule-based patterns"""
        facts = []
        text = parsed_doc.get("text", "")
        title = parsed_doc.get("title", "")
        
        # Combine text sources
        combined_text = f"{title} {text}"
        
        # Also check table data
        table_text = ""
        for table in parsed_doc.get("tables", []):
            for row in table.get("rows", []):
                if isinstance(row, dict):
                    table_text += " ".join(str(v) for v in row.values()) + " "
                elif isinstance(row, list):
                    table_text += " ".join(str(v) for v in row) + " "
        
        combined_text += " " + table_text
        
        # Extract facts for each metric
        for metric, patterns in self.patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                unit = pattern_info["unit"]
                base_confidence = pattern_info["confidence"]
                
                matches = re.finditer(pattern, combined_text, re.IGNORECASE)
                
                for match in matches:
                    try:
                        value_str = match.group(1).replace(',', '')
                        value = float(value_str)
                        
                        # Extract surrounding context
                        start = max(0, match.start() - 50)
                        end = min(len(combined_text), match.end() + 50)
                        span_excerpt = combined_text[start:end].strip()
                        
                        fact = ExtractedFact(
                            metric=metric,
                            value=value,
                            unit=unit,
                            span_excerpt=span_excerpt,
                            confidence=base_confidence,
                            extraction_method="rule_based"
                        )
                        
                        facts.append(fact)
                        
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Failed to extract value from match: {e}")
                        continue
        
        return facts

class TeslaFactExtractor(RuleBasedExtractor):
    """Tesla-specific fact extractor with enhanced patterns"""
    
    def __init__(self):
        super().__init__()
        self.tesla_patterns = self._load_tesla_patterns()
        self.patterns.update(self.tesla_patterns)
    
    def _load_tesla_patterns(self) -> Dict[str, List[Dict]]:
        """Load Tesla-specific extraction patterns"""
        return {
            "powerwall_capacity": [
                {
                    "pattern": r"Powerwall\s*(?:3|2)?\s*(?:has\s*)?(\d+\.?\d*)\s*kWh",
                    "unit": "kWh",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+\.?\d*)\s*kWh\s*Powerwall",
                    "unit": "kWh",
                    "confidence": 0.9
                }
            ],
            "solar_panel_power": [
                {
                    "pattern": r"Tesla\s*Solar\s*Panel[s]?\s*(?:produce\s*)?(\d+)\s*W",
                    "unit": "W",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+)\s*watt\s*Tesla\s*(?:solar\s*)?panel",
                    "unit": "W",
                    "confidence": 0.9
                }
            ],
            "solar_roof_power": [
                {
                    "pattern": r"Solar\s*Roof\s*(?:tile\s*)?(?:generates\s*)?(\d+\.?\d*)\s*W",
                    "unit": "W",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+\.?\d*)\s*watts?\s*per\s*(?:solar\s*)?tile",
                    "unit": "W",
                    "confidence": 0.9
                }
            ],
            "megapack_capacity": [
                {
                    "pattern": r"Megapack\s*(?:has\s*)?(\d+\.?\d*)\s*MWh",
                    "unit": "MWh",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+\.?\d*)\s*MWh\s*Megapack",
                    "unit": "MWh",
                    "confidence": 0.9
                }
            ],
            "backup_hours": [
                {
                    "pattern": r"(?:up\s*to\s*)?(\d+)\s*hours?\s*(?:of\s*)?backup",
                    "unit": "hours",
                    "confidence": 0.8
                },
                {
                    "pattern": r"backup\s*(?:power\s*)?(?:for\s*)?(\d+)\s*hours?",
                    "unit": "hours",
                    "confidence": 0.85
                }
            ]
        }
    
    def extract_facts(self, parsed_doc: Dict[str, Any]) -> List[ExtractedFact]:
        """Extract facts with Tesla-specific enhancements"""
        facts = super().extract_facts(parsed_doc)
        
        # Add Tesla-specific context analysis
        text = parsed_doc.get("text", "").lower()
        title = parsed_doc.get("title", "").lower()
        
        # Boost confidence for Tesla-related content
        tesla_keywords = ["tesla", "powerwall", "solar roof", "megapack", "solar panel"]
        is_tesla_content = any(keyword in f"{title} {text}" for keyword in tesla_keywords)
        
        if is_tesla_content:
            for fact in facts:
                if any(tesla_term in fact.span_excerpt.lower() for tesla_term in tesla_keywords):
                    fact.confidence = min(0.98, fact.confidence + 0.1)
                    fact.source_section = "tesla_product"
        
        return facts

class LLMFactExtractor(FactExtractor):
    """LLM-based fact extractor using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        
        if api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=api_key)
            except ImportError:
                logger.warning("OpenAI library not available")
    
    def extract_facts(self, parsed_doc: Dict[str, Any]) -> List[ExtractedFact]:
        """Extract facts using LLM"""
        if not self.client:
            logger.warning("LLM client not available, skipping LLM extraction")
            return []
        
        try:
            text = parsed_doc.get("text", "")[:4000]  # Limit text length
            title = parsed_doc.get("title", "")
            
            prompt = self._build_extraction_prompt(title, text)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting technical specifications from energy system documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            return self._parse_llm_response(result)
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []
    
    def _build_extraction_prompt(self, title: str, text: str) -> str:
        """Build extraction prompt for LLM"""
        return f"""
Extract technical specifications from this energy system document.

Title: {title}

Text: {text}

Please extract the following types of specifications if present:
- capacity_kwh: Energy storage capacity in kWh
- power_kw: Power rating in kW  
- efficiency_percent: Round-trip efficiency as percentage
- warranty_years: Warranty period in years
- cycle_life: Battery cycle life
- price_usd: Price in USD

Return results as JSON array with this format:
[
  {{
    "metric": "capacity_kwh",
    "value": 13.5,
    "unit": "kWh", 
    "span_excerpt": "13.5 kWh usable capacity",
    "confidence": 0.9
  }}
]

Only include specifications that are clearly stated in the text.
"""
    
    def _parse_llm_response(self, response: str) -> List[ExtractedFact]:
        """Parse LLM response into ExtractedFact objects"""
        try:
            data = json.loads(response)
            facts = []
            
            for item in data:
                fact = ExtractedFact(
                    metric=item["metric"],
                    value=float(item["value"]),
                    unit=item["unit"],
                    span_excerpt=item["span_excerpt"],
                    confidence=float(item["confidence"]),
                    extraction_method="llm"
                )
                facts.append(fact)
            
            return facts
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

class HybridFactExtractor(FactExtractor):
    """Hybrid extractor combining rule-based and LLM approaches"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.rule_extractor = TeslaFactExtractor()
        self.llm_extractor = LLMFactExtractor(api_key) if api_key else None
    
    def extract_facts(self, parsed_doc: Dict[str, Any]) -> List[ExtractedFact]:
        """Extract facts using both rule-based and LLM methods"""
        all_facts = []
        
        # Get rule-based facts
        rule_facts = self.rule_extractor.extract_facts(parsed_doc)
        all_facts.extend(rule_facts)
        
        # Get LLM facts if available
        if self.llm_extractor:
            llm_facts = self.llm_extractor.extract_facts(parsed_doc)
            all_facts.extend(llm_facts)
        
        # Deduplicate and merge facts
        return self._deduplicate_facts(all_facts)
    
    def _deduplicate_facts(self, facts: List[ExtractedFact]) -> List[ExtractedFact]:
        """Remove duplicate facts and merge similar ones"""
        deduplicated = {}
        
        for fact in facts:
            key = f"{fact.metric}_{fact.value}_{fact.unit}"
            
            if key not in deduplicated:
                deduplicated[key] = fact
            else:
                # Keep the fact with higher confidence
                existing = deduplicated[key]
                if fact.confidence > existing.confidence:
                    deduplicated[key] = fact
                elif fact.confidence == existing.confidence:
                    # Merge extraction methods
                    existing.extraction_method = f"{existing.extraction_method}+{fact.extraction_method}"
        
        return list(deduplicated.values())
