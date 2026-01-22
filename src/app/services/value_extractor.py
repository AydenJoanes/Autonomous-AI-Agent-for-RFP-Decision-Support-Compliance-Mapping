"""
Value Extractor Service
Extracts specific values (budget, timeline, certification, technology) from requirement text.
"""

import re
from typing import Optional, Dict
from loguru import logger


class ValueExtractor:
    """Extract structured values from unstructured requirement text."""

    def extract_budget(self, requirement_text: str) -> Optional[str]:
        """
        Extract dollar amount from requirement text.
        
        Args:
            requirement_text: The requirement text to extract from
            
        Returns:
            Normalized budget string (e.g., "150000") or None if not found
        """
        if not requirement_text:
            return None
        
        text = requirement_text.strip()
        
        # Pattern 1: $150,000 or $150,000.00
        pattern1 = r'\$[\d,]+(?:\.\d{2})?'
        match = re.search(pattern1, text)
        if match:
            value = match.group(0)
            # Remove $ and commas, convert to string
            normalized = value.replace('$', '').replace(',', '').split('.')[0]
            logger.info(f'[EXTRACTOR] Budget extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # Pattern 2: 150000 USD or 150,000 dollars
        pattern2 = r'(\d+(?:,\d{3})*)\s*(?:USD|dollars)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            normalized = value.replace(',', '')
            logger.info(f'[EXTRACTOR] Budget extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # Pattern 3: 150k or 150K
        pattern3 = r'(\d+)\s*[kK]'
        match = re.search(pattern3, text)
        if match:
            value = int(match.group(1)) * 1000
            normalized = str(value)
            logger.info(f'[EXTRACTOR] Budget extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # Pattern 4: 1.5M or 1.5 million
        pattern4 = r'(\d+(?:\.\d+)?)\s*[mM](?:illion)?'
        match = re.search(pattern4, text)
        if match:
            value = float(match.group(1)) * 1_000_000
            normalized = str(int(value))
            logger.info(f'[EXTRACTOR] Budget extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # No match found
        logger.debug(f'[EXTRACTOR] No budget found in "{text[:50]}..."')
        return None

    def extract_timeline(self, requirement_text: str) -> Optional[str]:
        """
        Extract duration from requirement text.
        
        Args:
            requirement_text: The requirement text to extract from
            
        Returns:
            Normalized timeline string (e.g., "4 months") or None if not found
        """
        if not requirement_text:
            return None
        
        text = requirement_text.strip()
        
        # Pattern 1: X months
        pattern_months = r'(\d+)\s*months?'
        match = re.search(pattern_months, text, re.IGNORECASE)
        if match:
            months = int(match.group(1))
            normalized = f"{months} months"
            logger.info(f'[EXTRACTOR] Timeline extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # Pattern 2: X weeks → convert to months
        pattern_weeks = r'(\d+)\s*weeks?'
        match = re.search(pattern_weeks, text, re.IGNORECASE)
        if match:
            weeks = int(match.group(1))
            months = int(weeks / 4.33)
            normalized = f"{months} months"
            logger.info(f'[EXTRACTOR] Timeline extracted: {normalized} (from {weeks} weeks) from "{text[:50]}..."')
            return normalized
        
        # Pattern 3: X years → convert to months
        pattern_years = r'(\d+)\s*years?'
        match = re.search(pattern_years, text, re.IGNORECASE)
        if match:
            years = int(match.group(1))
            months = years * 12
            normalized = f"{months} months"
            logger.info(f'[EXTRACTOR] Timeline extracted: {normalized} (from {years} years) from "{text[:50]}..."')
            return normalized
        
        # Pattern 4: X days → convert to months
        pattern_days = r'(\d+)\s*days?'
        match = re.search(pattern_days, text, re.IGNORECASE)
        if match:
            days = int(match.group(1))
            months = max(1, int(days / 30))  # Minimum 1 month
            normalized = f"{months} months"
            logger.info(f'[EXTRACTOR] Timeline extracted: {normalized} (from {days} days) from "{text[:50]}..."')
            return normalized
        
        # No match found
        logger.debug(f'[EXTRACTOR] No timeline found in "{text[:50]}..."')
        return None

    def extract_certification(self, requirement_text: str) -> Optional[str]:
        """
        Extract certification name from requirement text.
        
        Args:
            requirement_text: The requirement text to extract from
            
        Returns:
            Normalized certification name or None if not found
        """
        if not requirement_text:
            return None
        
        text = requirement_text.strip()
        
        # Pattern 1: ISO 27001, ISO 9001, etc.
        pattern_iso = r'ISO\s*\d+'
        match = re.search(pattern_iso, text, re.IGNORECASE)
        if match:
            normalized = match.group(0).upper().replace(' ', ' ')
            logger.info(f'[EXTRACTOR] Certification extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # Pattern 2: SOC 2, SOC 2 Type II, etc.
        pattern_soc = r'SOC\s*[12](?:\s*Type\s*(?:II|I|2|1))?' # II before I for longest match
        match = re.search(pattern_soc, text, re.IGNORECASE)
        if match:
            normalized = match.group(0).upper()
            logger.info(f'[EXTRACTOR] Certification extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # Pattern 3: PCI-DSS or PCI DSS
        pattern_pci = r'PCI[\s-]*DSS'
        match = re.search(pattern_pci, text, re.IGNORECASE)
        if match:
            normalized = "PCI-DSS"
            logger.info(f'[EXTRACTOR] Certification extracted: {normalized} from "{text[:50]}..."')
            return normalized
        
        # Pattern 4: HIPAA
        if re.search(r'\bHIPAA\b', text, re.IGNORECASE):
            logger.info(f'[EXTRACTOR] Certification extracted: HIPAA from "{text[:50]}..."')
            return "HIPAA"
        
        # Pattern 5: GDPR
        if re.search(r'\bGDPR\b', text, re.IGNORECASE):
            logger.info(f'[EXTRACTOR] Certification extracted: GDPR from "{text[:50]}..."')
            return "GDPR"
        
        # Pattern 6: FedRAMP
        if re.search(r'\bFedRAMP\b', text, re.IGNORECASE):
            logger.info(f'[EXTRACTOR] Certification extracted: FedRAMP from "{text[:50]}..."')
            return "FedRAMP"
        
        # No match found
        logger.debug(f'[EXTRACTOR] No certification found in "{text[:50]}..."')
        return None

    def extract_technology(self, requirement_text: str) -> Optional[str]:
        """
        Extract technology name from requirement text.
        
        Args:
            requirement_text: The requirement text to extract from
            
        Returns:
            Normalized technology name or None if not found
        """
        if not requirement_text:
            return None
        
        text = requirement_text.strip()
        
        # Known technology patterns by category
        technologies = {
            # Programming Languages
            "Python": r'\bPython\b',
            "Java": r'\bJava\b(?!Script)',
            "JavaScript": r'\bJavaScript\b|\bJS\b',
            "TypeScript": r'\bTypeScript\b|\bTS\b',
            "SQL": r'\bSQL\b',
            "C#": r'\bC#\b|\.NET',
            "Go": r'\bGolang\b|\bGo\b',
            "Rust": r'\bRust\b',
            "Ruby": r'\bRuby\b',
            "PHP": r'\bPHP\b',
            
            # Frameworks
            "React": r'\bReact\b',
            "Angular": r'\bAngular\b',
            "Vue": r'\bVue\.?js?\b|\bVue\b',
            "Django": r'\bDjango\b',
            "FastAPI": r'\bFastAPI\b',
            "Flask": r'\bFlask\b',
            "Spring": r'\bSpring\b',
            "Node.js": r'\bNode\.?js\b|\bNodeJS\b',
            "Express": r'\bExpress\b',
            
            # Cloud Platforms
            "AWS": r'\bAWS\b|\bAmazon Web Services\b',
            "Azure": r'\bAzure\b|\bMicrosoft Azure\b',
            "GCP": r'\bGCP\b|\bGoogle Cloud\b',
            "Kubernetes": r'\bKubernetes\b|\bK8s\b',
            "Docker": r'\bDocker\b',
            
            # Databases
            "PostgreSQL": r'\bPostgreSQL\b|\bPostgres\b',
            "MySQL": r'\bMySQL\b',
            "MongoDB": r'\bMongoDB\b|\bMongo\b',
            "Redis": r'\bRedis\b',
            "Elasticsearch": r'\bElasticsearch\b|\bElastic\b',
            "Oracle": r'\bOracle\b',
            
            # AI/ML
            "TensorFlow": r'\bTensorFlow\b',
            "PyTorch": r'\bPyTorch\b',
            "LangChain": r'\bLangChain\b',
            "OpenAI": r'\bOpenAI\b',
            "Scikit-learn": r'\bscikit-learn\b|\bsklearn\b',
            "Hugging Face": r'\bHugging\s*Face\b',
        }
        
        for tech_name, pattern in technologies.items():
            if re.search(pattern, text, re.IGNORECASE):
                logger.info(f'[EXTRACTOR] Technology extracted: {tech_name} from "{text[:50]}..."')
                return tech_name
        
        # No match found
        logger.debug(f'[EXTRACTOR] No technology found in "{text[:50]}..."')
        return None

    def extract_all(self, requirement_text: str) -> Dict[str, Optional[str]]:
        """
        Extract all possible values from requirement text.
        
        Args:
            requirement_text: The requirement text to extract from
            
        Returns:
            Dictionary with all extracted values
        """
        return {
            "budget": self.extract_budget(requirement_text),
            "timeline": self.extract_timeline(requirement_text),
            "certification": self.extract_certification(requirement_text),
            "technology": self.extract_technology(requirement_text)
        }

