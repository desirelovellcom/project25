"""
Document parsing utilities for HTML, PDF, and other formats
"""

import re
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse
import hashlib

try:
    import trafilatura
    from trafilatura.settings import use_config
except ImportError:
    trafilatura = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)

class DocumentParser(ABC):
    """Abstract base class for document parsers"""
    
    @abstractmethod
    def parse(self, content: str, url: str = None) -> Dict[str, Any]:
        """Parse document content and extract structured data"""
        pass

class HTMLParser(DocumentParser):
    """HTML document parser using trafilatura and BeautifulSoup"""
    
    def __init__(self):
        self.config = None
        if trafilatura:
            self.config = use_config()
            self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
    
    def parse(self, content: str, url: str = None) -> Dict[str, Any]:
        """Parse HTML content and extract clean text, metadata, and structured data"""
        try:
            result = {
                "title": "",
                "text": "",
                "metadata": {},
                "tables": [],
                "links": [],
                "images": [],
                "specifications": {}
            }
            
            # Use trafilatura for main content extraction
            if trafilatura:
                extracted_text = trafilatura.extract(
                    content, 
                    config=self.config,
                    include_tables=True,
                    include_links=True,
                    include_images=True
                )
                if extracted_text:
                    result["text"] = extracted_text
                
                # Extract metadata
                metadata = trafilatura.extract_metadata(content)
                if metadata:
                    result["metadata"] = {
                        "title": metadata.title,
                        "author": metadata.author,
                        "date": metadata.date,
                        "description": metadata.description,
                        "sitename": metadata.sitename,
                        "categories": metadata.categories,
                        "tags": metadata.tags
                    }
                    if metadata.title:
                        result["title"] = metadata.title
            
            # Use BeautifulSoup for additional structured data extraction
            if BeautifulSoup:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract title if not found
                if not result["title"]:
                    title_tag = soup.find('title')
                    if title_tag:
                        result["title"] = title_tag.get_text().strip()
                
                # Extract tables for specifications
                tables = soup.find_all('table')
                for table in tables:
                    table_data = self._parse_table(table)
                    if table_data:
                        result["tables"].append(table_data)
                
                # Extract links
                links = soup.find_all('a', href=True)
                for link in links[:50]:  # Limit to first 50 links
                    href = link['href']
                    if url:
                        href = urljoin(url, href)
                    result["links"].append({
                        "text": link.get_text().strip(),
                        "href": href
                    })
                
                # Extract images
                images = soup.find_all('img', src=True)
                for img in images[:20]:  # Limit to first 20 images
                    src = img['src']
                    if url:
                        src = urljoin(url, src)
                    result["images"].append({
                        "src": src,
                        "alt": img.get('alt', ''),
                        "title": img.get('title', '')
                    })
                
                # Extract Tesla-specific specifications
                result["specifications"] = self._extract_tesla_specs(soup, result["text"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            return {
                "title": "",
                "text": content[:1000] if content else "",  # Fallback to raw content
                "metadata": {},
                "tables": [],
                "links": [],
                "images": [],
                "specifications": {}
            }
    
    def _parse_table(self, table) -> Optional[Dict[str, Any]]:
        """Parse HTML table into structured data"""
        try:
            rows = []
            headers = []
            
            # Extract headers
            header_row = table.find('tr')
            if header_row:
                header_cells = header_row.find_all(['th', 'td'])
                headers = [cell.get_text().strip() for cell in header_cells]
            
            # Extract data rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text().strip() for cell in cells]
                    if len(row_data) == len(headers):
                        rows.append(dict(zip(headers, row_data)))
                    else:
                        rows.append(row_data)
            
            if rows:
                return {
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows)
                }
            
        except Exception as e:
            logger.warning(f"Error parsing table: {e}")
        
        return None
    
    def _extract_tesla_specs(self, soup, text: str) -> Dict[str, Any]:
        """Extract Tesla-specific technical specifications"""
        specs = {}
        
        # Common Tesla specification patterns
        patterns = {
            "capacity_kwh": [
                r"(\d+\.?\d*)\s*kWh",
                r"(\d+\.?\d*)\s*kilowatt.?hour",
                r"capacity[:\s]*(\d+\.?\d*)\s*kWh"
            ],
            "power_kw": [
                r"(\d+\.?\d*)\s*kW(?!h)",
                r"(\d+\.?\d*)\s*kilowatt(?!.?hour)",
                r"power[:\s]*(\d+\.?\d*)\s*kW"
            ],
            "efficiency_percent": [
                r"(\d+\.?\d*)%\s*efficiency",
                r"efficiency[:\s]*(\d+\.?\d*)%",
                r"(\d+\.?\d*)\s*percent\s*efficient"
            ],
            "warranty_years": [
                r"(\d+).?year\s*warranty",
                r"warranty[:\s]*(\d+)\s*years?",
                r"guaranteed\s*for\s*(\d+)\s*years?"
            ],
            "price_usd": [
                r"\$(\d+,?\d*)",
                r"(\d+,?\d*)\s*USD",
                r"price[:\s]*\$(\d+,?\d*)"
            ]
        }
        
        combined_text = f"{text} {soup.get_text()}"
        
        for spec_name, regex_patterns in patterns.items():
            for pattern in regex_patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    try:
                        # Take the first match and clean it
                        value = matches[0].replace(',', '')
                        specs[spec_name] = float(value)
                        break
                    except (ValueError, TypeError):
                        continue
        
        return specs

class PDFParser(DocumentParser):
    """PDF document parser"""
    
    def parse(self, content: bytes, url: str = None) -> Dict[str, Any]:
        """Parse PDF content and extract text"""
        try:
            if not PyPDF2:
                logger.warning("PyPDF2 not available, cannot parse PDF")
                return {"title": "", "text": "", "metadata": {}}
            
            # This would implement PDF parsing
            # For now, return empty structure
            return {
                "title": "",
                "text": "",
                "metadata": {},
                "tables": [],
                "specifications": {}
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF content: {e}")
            return {"title": "", "text": "", "metadata": {}}

class DocumentParserFactory:
    """Factory for creating appropriate document parsers"""
    
    @staticmethod
    def get_parser(content_type: str) -> DocumentParser:
        """Get appropriate parser based on content type"""
        if content_type.startswith('text/html'):
            return HTMLParser()
        elif content_type == 'application/pdf':
            return PDFParser()
        else:
            # Default to HTML parser for unknown types
            return HTMLParser()
