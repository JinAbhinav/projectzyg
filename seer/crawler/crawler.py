"""
Simple HTTP-based web crawler module that doesn't rely on Playwright.
Handles basic web crawling with HTTP requests instead of browser automation.
"""

import os
import asyncio
import logging
import re
import httpx
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from markdownify import markdownify

# Try to import markdown, but use a fallback if not available
try:
    from markdown import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    logging.warning("Markdown package not found, will use simple text extraction instead")

from ..utils.config import settings
from seer.schemas.crawl_schemas import (
    CrawlParameters,
    CrawlResult,
    WebPage,
    WebPageMetadata
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default output directory for crawled content
DEFAULT_OUTPUT_DIR = Path("./crawled_data")

# List of user agents for rotating to avoid being blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

class CrawlResult:
    """Class to hold the results of a crawl operation."""
    
    def __init__(self, status: str, results: List[Any], url: str = None, message: str = None, metadata: Dict[str, Any] = None):
        self.status = status
        self.results = results
        self.url = url
        self.message = message
        self.metadata = metadata or {}
        # Add 'pages' property for backward compatibility
        self.pages = results

    def __getattr__(self, name):
        # Handle backward compatibility where code expects certain attributes
        if name == 'pages':
            return self.results
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "status": self.status,
            "results": self.results,
            "url": self.url,
            "message": self.message,
            "metadata": self.metadata
        }

class SimpleWebCrawler:
    """A simple HTTP-based web crawler that doesn't rely on browser automation."""
    
    def __init__(self, max_pages: int = 10, max_depth: int = 3):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls = set()
        self.results = []
        self.user_agents = USER_AGENTS
        self.logger = logging.getLogger(__name__)

    def _get_random_user_agent(self):
        """Return a random user agent to avoid blocking."""
        return random.choice(USER_AGENTS)
        
    def _get_random_headers(self):
        """Return random headers with user agent to avoid blocking."""
        return {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
    async def crawl(self, url: str, parameters: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """Crawl a website and extract content."""
        self.logger.info(f"Starting crawl of {url} with max_pages={self.max_pages}, max_depth={self.max_depth}")
        
        start_time = datetime.now()
        self.results = []
        self.visited_urls = set()
        
        try:
            # Start the recursive crawl from the root URL with depth 0
            await self._crawl_recursive(url, 0, 0)
            
            end_time = datetime.now()
            
            # Return successful result
            return CrawlResult(
                status="success",
                results=self.results,
                url=url,
                metadata={
                    "url": url,
                    "pages_crawled": len(self.results),
                    "execution_time": (end_time - start_time).total_seconds(),
                    "max_depth": self.max_depth,
                    "max_pages": self.max_pages
                }
            )
        except Exception as e:
            self.logger.error(f"Error during crawl: {str(e)}")
            return CrawlResult(
                status="error",
                results=[],
                url=url,
                message=str(e)
            )
    
    async def _crawl_recursive(self, url: str, depth: int = 0, visited_count: int = 0):
        """Crawl a webpage and extract content recursively."""
        if (
            depth > self.max_depth 
            or visited_count >= self.max_pages 
            or url in self.visited_urls
        ):
            return visited_count
            
        self.logger.info(f"Crawling {url} at depth {depth}")
        self.visited_urls.add(url)
        
        try:
            headers = self._get_random_headers()
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract main content, convert to markdown
                try:
                    # Extract content
                    main_content = self._extract_main_content(soup)
                    if not main_content:
                        main_content = soup.get_text(" ", strip=True)
                        
                    # Convert to markdown
                    markdown_content = self._html_to_markdown(main_content)
                    
                    # Extract title with error handling
                    title = ""
                    if soup.title and soup.title.string:
                        title = soup.title.string
                    else:
                        # Try to find h1 as fallback
                        h1 = soup.find('h1')
                        if h1:
                            title = h1.get_text(strip=True)
                        else:
                            title = url.split('/')[-1] or "Untitled Page"
                    
                    # Get detailed metadata
                    try:
                        metadata = self._extract_detailed_metadata(soup, url)
                    except Exception as e:
                        self.logger.error(f"Error extracting detailed metadata: {str(e)}")
                        metadata = {}
                        
                    # Add basic metadata
                    metadata.update({
                        "crawled_at": datetime.now().isoformat(),
                        "depth": depth,
                        "last_fetched": datetime.now().isoformat()
                    })
                    
                    # Add the page to results
                    self.results.append({
                        "url": url,
                        "title": title,
                        "content": markdown_content,
                        "content_type": "text/markdown",
                        "metadata": metadata,
                        "page_metadata": metadata  # Add duplicate for compatibility
                    })
                    
                    visited_count += 1
                    
                    # Only crawl links if not at max depth
                    if depth < self.max_depth and visited_count < self.max_pages:
                        try:
                            links = self._extract_links(soup, url)
                            if links:
                                metadata["links"] = links
                                
                                # Sort links to prioritize shorter paths
                                sorted_links = sorted(links, key=lambda x: len(x.split('/')))
                                
                                # Crawl further pages
                                for link in sorted_links:
                                    if visited_count >= self.max_pages:
                                        break
                                        
                                    # Add a small delay to avoid overwhelming the server
                                    await asyncio.sleep(0.5)
                                    
                                    visited_count = await self._crawl_recursive(
                                        link, 
                                        depth=depth+1, 
                                        visited_count=visited_count
                                    )
                        except Exception as e:
                            self.logger.error(f"Error extracting links from {url}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Error crawling {url}: {str(e)}")
                
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error for {url}: {e.response.status_code}")
        except httpx.RequestError as e:
            self.logger.error(f"Request error for {url}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            
        return visited_count
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content from the webpage with improved content detection."""
        # Try to find main content area
        main_content = None
        
        # First, remove obvious noise elements
        if soup and soup.body:
            for noise in soup.select('script, style, meta, link, noscript, iframe, [class*="ad"], [class*="banner"], [id*="ad"], [id*="banner"]'):
                noise.decompose()
            
            # Look for common main content containers with a better priority order
            content_selectors = [
                'article', 'main', '#content', '.content', '#main-content', '.main-content',
                '.post-content', '.entry-content', '.article-content', '#primary',
                'section', '.page-content', '#main', '.main'
            ]
            
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content and len(content.get_text(strip=True)) > 200:  # Ensure it has meaningful content
                    main_content = content
                    break
            
            # If no specific main content found, try to identify the content area with most text
            if not main_content:
                candidates = []
                for div in soup.find_all(['div', 'section']):
                    text_length = len(div.get_text(strip=True))
                    # Ignore very short sections or very large sections (likely the whole page)
                    if 200 < text_length < 20000:
                        candidates.append((div, text_length))
                
                # Sort by text length and pick the top one
                if candidates:
                    candidates.sort(key=lambda x: x[1], reverse=True)
                    main_content = candidates[0][0]
            
            # If still no main content found, use the body but filter it
            if not main_content:
                main_content = soup.body
            
            # Remove remaining noise elements from the selected content
            if main_content:
                for element in main_content.select('nav, footer, header, .sidebar, .footer, .header, .navigation, .menu, .comments'):
                    element.decompose()
                
                # Further clean up any elements that are likely navigation or ads
                for element in main_content.find_all(['div', 'section']):
                    if element.get('class') or element.get('id'):
                        attr_text = str(element.get('class', '')) + str(element.get('id', ''))
                        if any(noise_term in attr_text for noise_term in 
                            ['nav', 'menu', 'sidebar', 'comment', 'footer', 'header', 'banner', 'ad-']):
                            element.decompose()
                
                return str(main_content)
        return "<p>No content could be extracted from this page.</p>"
    
    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to simple markdown format without external dependencies."""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script, style and other non-content elements
            for tag in soup.find_all(['script', 'style', 'meta', 'link', 'noscript', 'iframe']):
                tag.decompose()
            
            # Process headings (h1-h6)
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    text = heading.get_text(strip=True)
                    heading.replace_with(BeautifulSoup(f"\n{'#' * i} {text}\n\n", 'html.parser'))
            
            # Process paragraphs
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    p.replace_with(BeautifulSoup(f"\n{text}\n\n", 'html.parser'))
            
            # Process lists
            for ul in soup.find_all('ul'):
                list_items = []
                for li in ul.find_all('li'):
                    text = li.get_text(strip=True)
                    if text:
                        list_items.append(f"* {text}")
                ul.replace_with(BeautifulSoup(f"\n{chr(10).join(list_items)}\n\n", 'html.parser'))
            
            # Process ordered lists
            for ol in soup.find_all('ol'):
                list_items = []
                for i, li in enumerate(ol.find_all('li')):
                    text = li.get_text(strip=True)
                    if text:
                        list_items.append(f"{i+1}. {text}")
                ol.replace_with(BeautifulSoup(f"\n{chr(10).join(list_items)}\n\n", 'html.parser'))
            
            # Process links
            for a in soup.find_all('a'):
                text = a.get_text(strip=True)
                href = a.get('href', '')
                if text and href:
                    a.replace_with(BeautifulSoup(f"[{text}]({href})", 'html.parser'))
            
            # Process images
            for img in soup.find_all('img'):
                alt = img.get('alt', 'Image')
                src = img.get('src', '')
                if src:
                    img.replace_with(BeautifulSoup(f"![{alt}]({src})", 'html.parser'))
            
            # Get plain text content
            text = soup.get_text(separator='\n\n')
            
            # Clean up whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)
            
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error converting HTML to markdown: {str(e)}")
            # Fallback to simple text extraction
            try:
                return BeautifulSoup(html_content, 'html.parser').get_text(separator='\n\n')
            except:
                return "Error extracting content"
                
    def _convert_to_markdown(self, html_content: str) -> str:
        """Alias for _html_to_markdown to maintain backward compatibility."""
        return self._html_to_markdown(html_content)
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from the webpage."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and 'content' in meta_desc.attrs:
            return meta_desc['content']
        return ""
    
    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract language from the webpage."""
        html_tag = soup.find('html')
        if html_tag and 'lang' in html_tag.attrs:
            return html_tag['lang']
        return "en"  # Default to English
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from the webpage with improved error handling."""
        links = []
        
        if not soup or not base_url:
            return links
            
        try:
            domain = urlparse(base_url).netloc
            
            if not domain:
                return links
                
            # First pass - collect menu/navigation links as priority
            nav_element = soup.select_one('nav, header, .navigation, .menu, [class*="nav-"], [class*="menu-"]')
            if nav_element:
                for a_tag in nav_element.find_all('a', href=True):
                    href = a_tag.get('href')
                    
                    # Skip empty links, anchors, or javascript
                    if not href or href.startswith('#') or href.startswith('javascript:'):
                        continue
                    
                    # Resolve relative URLs
                    try:
                        full_url = urljoin(base_url, href)
                        parsed_url = urlparse(full_url)
                        
                        # Only include links from the same domain
                        if parsed_url.netloc == domain:
                            # Remove fragments
                            clean_url = parsed_url._replace(fragment='').geturl()
                            
                            if clean_url not in self.visited_urls:
                                links.append(clean_url)
                    except Exception as e:
                        self.logger.error(f"Error processing nav link {href}: {str(e)}")
                        continue
            
            # Second pass - collect all remaining links
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href')
                
                # Skip empty links, anchors, or javascript
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                
                # Resolve relative URLs
                try:
                    full_url = urljoin(base_url, href)
                    parsed_url = urlparse(full_url)
                    
                    # Only include links from the same domain
                    if parsed_url.netloc == domain:
                        # Remove fragments
                        clean_url = parsed_url._replace(fragment='').geturl()
                        
                        if clean_url not in self.visited_urls and clean_url not in links:
                            links.append(clean_url)
                except Exception as e:
                    self.logger.error(f"Error processing link {href}: {str(e)}")
                    continue
        except Exception as e:
            self.logger.error(f"Error extracting links from {base_url}: {str(e)}")
            
        return links
    
    def _extract_detailed_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract detailed metadata from the webpage."""
        metadata = {}
        
        # Safety checks
        if not soup:
            return metadata
            
        try:
            # Extract all meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                # Fix the argument conflict issue
                if meta.has_attr('name'):
                    meta_tags[meta.get('name')] = meta.get('content', '')
                elif meta.has_attr('property'):
                    meta_tags[meta.get('property')] = meta.get('content', '')
            
            # Add meta tags to metadata
            metadata['meta_tags'] = meta_tags
            
            # Extract favicon
            favicon = ''
            favicon_tag = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            if favicon_tag and favicon_tag.get('href'):
                favicon = urljoin(url, favicon_tag.get('href', ''))
            metadata['favicon'] = favicon
            
            # Extract canonical URL
            canonical = ''
            canonical_tag = soup.find('link', rel='canonical')
            if canonical_tag and canonical_tag.get('href'):
                canonical = canonical_tag.get('href', '')
            metadata['canonical_url'] = canonical
            
            # Extract OpenGraph metadata
            og_metadata = {}
            for meta in soup.find_all('meta'):
                if meta.has_attr('property') and meta.get('property', '').startswith('og:'):
                    og_metadata[meta.get('property')] = meta.get('content', '')
            metadata['open_graph'] = og_metadata
            
            # Extract Twitter card metadata
            twitter_metadata = {}
            for meta in soup.find_all('meta'):
                if meta.has_attr('name') and meta.get('name', '').startswith('twitter:'):
                    twitter_metadata[meta.get('name')] = meta.get('content', '')
            metadata['twitter_card'] = twitter_metadata
            
            # Extract structured data (JSON-LD)
            structured_data = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    if script.string:
                        data = json.loads(script.string)
                        structured_data.append(data)
                except:
                    pass
            metadata['structured_data'] = structured_data
            
            # Count elements by type
            element_counts = {}
            for tag in ['p', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'form', 'input']:
                element_counts[tag] = len(soup.find_all(tag))
            metadata['element_counts'] = element_counts
            
            # Extract images
            images = []
            for img in soup.find_all('img'):
                if img.has_attr('src'):
                    img_url = urljoin(url, img.get('src', ''))
                    images.append({
                        'url': img_url,
                        'alt': img.get('alt', ''),
                        'width': img.get('width', ''),
                        'height': img.get('height', '')
                    })
            metadata['images'] = images[:20]  # Increase limit to 20 images
            
            # Extract main headings hierarchy
            headings = []
            for i in range(1, 7):
                for h in soup.find_all(f'h{i}'):
                    headings.append({
                        'level': i,
                        'text': h.get_text(strip=True)
                    })
            metadata['headings'] = headings
            
            # Extract course information (if present)
            courses = self._extract_courses(soup, url)
            if courses:
                metadata['courses'] = courses
            
            # Extract team/staff/mentor information (if present)
            people = self._extract_people(soup, url)
            if people:
                metadata['people'] = people
                
            # Extract pricing information (if present)
            pricing = self._extract_pricing(soup)
            if pricing:
                metadata['pricing'] = pricing
                
            # Extract contact information (if present)
            contact_info = self._extract_contact_info(soup)
            if contact_info:
                metadata['contact_info'] = contact_info
            
            # Page analysis
            text_content = soup.get_text(" ", strip=True)
            metadata['text_length'] = len(text_content)
            metadata['word_count'] = len(text_content.split())
            
            # Extract domain info
            parsed_url = urlparse(url)
            metadata['domain'] = parsed_url.netloc
            metadata['path'] = parsed_url.path
            
            # Extract navigation menu
            nav_items = self._extract_navigation(soup, url)
            if nav_items:
                metadata['navigation'] = nav_items
            
            # Attempt to detect page type
            page_type = self._detect_page_type(soup, url)
            metadata['page_type'] = page_type
            
        except Exception as e:
            self.logger.error(f"Error extracting detailed metadata: {str(e)}")
        
        return metadata
        
    def _extract_courses(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract course information from educational websites."""
        courses = []
        
        # Look for common course containers
        course_containers = []
        
        # Method 1: Look for course cards/sections with common class names
        for selector in [
            '.course', '.courses', '.course-card', '.course-item', '.program', 
            '.program-card', '[class*="course"]', '[class*="Course"]', 
            '[id*="course"]', '[id*="Course"]'
        ]:
            containers = soup.select(selector)
            if containers:
                course_containers.extend(containers)
        
        # Method 2: Look for structured sections that might be courses
        if not course_containers:
            # Find sections with images and headings that might be course cards
            sections = soup.find_all(['div', 'section', 'article'])
            for section in sections:
                if section.find('img') and section.find(['h2', 'h3', 'h4']):
                    course_containers.append(section)
        
        # Process each potential course container
        for container in course_containers:
            course = {}
            
            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if title_elem:
                course['title'] = title_elem.get_text(strip=True)
            else:
                continue  # Skip if no title found
            
            # Extract description
            desc_elem = container.find(['p', '.description', '[class*="description"]', '[class*="content"]'])
            if desc_elem:
                course['description'] = desc_elem.get_text(strip=True)
            
            # Extract price
            price_elem = container.select_one('[class*="price"], .price, [class*="cost"], .cost, [class*="fee"], .fee')
            if price_elem:
                course['price'] = price_elem.get_text(strip=True)
            
            # Extract image
            img_elem = container.find('img')
            if img_elem and img_elem.has_attr('src'):
                course['image'] = urljoin(base_url, img_elem['src'])
                
            # Extract link
            link_elem = container.find('a')
            if link_elem and link_elem.has_attr('href'):
                course['url'] = urljoin(base_url, link_elem['href'])
                
            # Extract duration
            duration_elem = container.select_one('[class*="duration"], .duration, [class*="time"], .time, [class*="length"], .length')
            if duration_elem:
                course['duration'] = duration_elem.get_text(strip=True)
                
            # Add to courses list if we have enough data
            if len(course) > 1:  # At least title and one other piece of info
                courses.append(course)
        
        return courses
        
    def _extract_people(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract information about people (team members, mentors, staff, etc.)."""
        people = []
        
        # Look for common people/team/staff containers
        people_containers = []
        
        # Method 1: Look for team sections with common class names
        for selector in [
            '.team', '.team-member', '.staff', '.faculty', '.instructor', 
            '.mentor', '.teacher', '.professor', '.tutor', '[class*="team"]', 
            '[class*="staff"]', '[class*="faculty"]', '[class*="people"]'
        ]:
            containers = soup.select(selector)
            if containers:
                people_containers.extend(containers)
                
        # Method 2: Look for structured sections that might contain people
        if not people_containers:
            # Find collections of similar structured elements that might be team members
            parent_elements = soup.find_all(['div', 'section', 'article'])
            for parent in parent_elements:
                child_elements = parent.find_all(['div', 'li', 'article'])
                if len(child_elements) >= 2:
                    # Check if these elements have similar structure (image + name)
                    if all(child.find('img') for child in child_elements) and all(child.find(['h3', 'h4', 'h5', 'strong', 'b']) for child in child_elements):
                        people_containers.extend(child_elements)
                        
        # Process each potential person container
        for container in people_containers:
            person = {}
            
            # Extract name
            name_elem = container.find(['h2', 'h3', 'h4', 'h5', 'strong', 'b', '.name', '[class*="name"]'])
            if name_elem:
                person['name'] = name_elem.get_text(strip=True)
            else:
                continue  # Skip if no name found
                
            # Extract title/role
            role_elem = container.select_one('.role, .title, .position, [class*="role"], [class*="title"], [class*="position"]')
            if role_elem:
                person['role'] = role_elem.get_text(strip=True)
                
            # Extract bio/description
            bio_elem = container.find(['p', '.bio', '.description', '[class*="bio"]', '[class*="description"]'])
            if bio_elem:
                person['bio'] = bio_elem.get_text(strip=True)
                
            # Extract image
            img_elem = container.find('img')
            if img_elem and img_elem.has_attr('src'):
                person['image'] = urljoin(base_url, img_elem['src'])
                
            # Extract social links
            social_links = {}
            for link in container.find_all('a'):
                href = link.get('href', '')
                if not href:
                    continue
                    
                # Check for common social media links
                for platform, pattern in [
                    ('linkedin', 'linkedin.com'),
                    ('twitter', 'twitter.com'),
                    ('x', 'x.com'),
                    ('facebook', 'facebook.com'),
                    ('instagram', 'instagram.com'),
                    ('github', 'github.com'),
                ]:
                    if pattern in href.lower():
                        social_links[platform] = href
                        break
                        
            if social_links:
                person['social_links'] = social_links
                
            # Add to people list if we have enough data
            if len(person) > 1:  # At least name and one other piece of info
                people.append(person)
                
        return people
        
    def _extract_pricing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract pricing information from the webpage."""
        pricing_plans = []
        
        # Look for common pricing container selectors
        pricing_containers = []
        
        for selector in [
            '.pricing', '.price', '.plan', '.package', '.subscription',
            '[class*="pricing"]', '[class*="price"]', '[class*="plan"]', 
            '[class*="package"]', '[class*="subscription"]'
        ]:
            containers = soup.select(selector)
            if containers:
                pricing_containers.extend(containers)
                
        # Method 2: Look for tables that might contain pricing
        pricing_tables = soup.select('table')
        
        # Process containers
        for container in pricing_containers:
            plan = {}
            
            # Extract plan name
            name_elem = container.find(['h2', 'h3', 'h4', '.name', '[class*="name"]', '[class*="title"]'])
            if name_elem:
                plan['name'] = name_elem.get_text(strip=True)
            else:
                continue  # Skip if no name found
                
            # Extract price
            price_elem = container.select_one('.price, [class*="price"], .cost, [class*="cost"], [class*="amount"]')
            if price_elem:
                plan['price'] = price_elem.get_text(strip=True)
                
            # Extract features
            features = []
            for feature_elem in container.select('li, .feature, [class*="feature"], .item, [class*="item"]'):
                feature_text = feature_elem.get_text(strip=True)
                if feature_text:
                    features.append(feature_text)
                    
            if features:
                plan['features'] = features
                
            # Add to pricing list if we have enough data
            if len(plan) > 1:  # At least name and one other piece of info
                pricing_plans.append(plan)
                
        # Process tables (if no containers found)
        if not pricing_plans and pricing_tables:
            for table in pricing_tables:
                # Extract headers
                headers = []
                for th in table.select('th'):
                    headers.append(th.get_text(strip=True))
                    
                # If no headers found, use first row as headers
                if not headers:
                    first_row = table.select_one('tr')
                    if first_row:
                        for td in first_row.select('td'):
                            headers.append(td.get_text(strip=True))
                
                # Process rows
                for row in table.select('tr')[1:] if headers else table.select('tr')[1:]:
                    cells = row.select('td')
                    if len(cells) > 1:
                        plan = {}
                        for i, cell in enumerate(cells):
                            if i < len(headers):
                                plan[headers[i]] = cell.get_text(strip=True)
                            else:
                                # If we run out of headers, use generic names
                                plan[f'column_{i+1}'] = cell.get_text(strip=True)
                                
                        if plan:
                            pricing_plans.append(plan)
                            
        return pricing_plans
        
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information from the webpage."""
        contact_info = {}
        
        # Look for email addresses
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, str(soup))
        if email_matches:
            contact_info['email'] = email_matches[0]  # Take the first email address
            
        # Look for phone numbers
        phone_pattern = r'(\+\d{1,3}[-\.\s]??)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}'
        phone_matches = re.findall(phone_pattern, str(soup))
        if phone_matches:
            contact_info['phone'] = phone_matches[0]
            
        # Look for physical address
        address_container = soup.select_one('address, .address, [class*="address"], [itemprop="address"]')
        if address_container:
            contact_info['address'] = address_container.get_text(strip=True)
            
        # Look for social media links
        social_links = {}
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if not href:
                continue
                
            # Check for common social media platforms
            for platform, pattern in [
                ('linkedin', 'linkedin.com'),
                ('twitter', 'twitter.com'),
                ('x', 'x.com'),
                ('facebook', 'facebook.com'),
                ('instagram', 'instagram.com'),
                ('youtube', 'youtube.com'),
                ('pinterest', 'pinterest.com'),
                ('github', 'github.com'),
            ]:
                if pattern in href.lower():
                    social_links[platform] = href
                    break
                    
        if social_links:
            contact_info['social_media'] = social_links
            
        # Look for contact form
        contact_form = soup.select_one('form:has(input[type="email"]), form[class*="contact"], form[id*="contact"]')
        if contact_form:
            contact_info['has_contact_form'] = True
            
        return contact_info
        
    def _extract_navigation(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract navigation menu items."""
        nav_items = []
        
        # Look for navigation elements
        nav_element = soup.select_one('nav, header, .navigation, .menu, [class*="nav-"], [class*="menu-"]')
        
        if nav_element:
            # Look for links in the navigation
            for link in nav_element.find_all('a'):
                href = link.get('href', '')
                if not href or href == '#' or href.startswith('javascript:'):
                    continue
                    
                text = link.get_text(strip=True)
                if not text:
                    continue
                    
                # Create absolute URL
                abs_url = urljoin(base_url, href)
                
                nav_items.append({
                    'text': text,
                    'url': abs_url
                })
                
        return nav_items
    
    def _detect_page_type(self, soup: BeautifulSoup, url: str) -> str:
        """Attempt to detect the type of page based on content and structure."""
        if not soup:
            return "Unknown"
            
        try:
            url_path = urlparse(url).path.lower()
            page_text = soup.get_text(" ", strip=True).lower()
            
            # Check URL patterns
            if url_path == "" or url_path == "/" or url_path.endswith("index.html"):
                return "Homepage"
                
            if any(term in url_path for term in ["/about", "/about-us"]):
                return "About Page"
                
            if any(term in url_path for term in ["/contact", "/contact-us"]):
                return "Contact Page"
                
            if any(term in url_path for term in ["/blog", "/news", "/article", "/post"]):
                return "Blog/Article"
                
            if any(term in url_path for term in ["/product", "/item", "/shop"]):
                return "Product Page"
                
            if any(term in url_path for term in ["/category", "/collection"]):
                return "Category Page"
                
            if any(term in url_path for term in ["/privacy", "/terms", "/tos"]):
                return "Legal Page"
                
            # Check content patterns
            if "404" in page_text and "not found" in page_text:
                return "Error Page"
                
            if any(term in page_text for term in ["add to cart", "buy now", "price", "$", "€"]):
                return "Product Page"
                
            if any(term in page_text for term in ["contact us", "get in touch", "send us a message"]):
                return "Contact Page"
                
            if any(term in page_text for term in ["privacy policy", "terms of service", "terms and conditions"]):
                return "Legal Page"
                
            if any(term in page_text for term in ["about us", "our mission", "our team", "our story"]):
                return "About Page"
                
            # Check for forms
            if soup.find('form'):
                if soup.find('input', {'type': 'password'}):
                    return "Login/Registration Page"
                if soup.find('textarea'):
                    return "Contact Page"
                    
            # Default
            return "Content Page"
        except Exception as e:
            self.logger.error(f"Error detecting page type: {str(e)}")
            return "Unknown"


async def perform_crawl(url, parameters=None):
    """Perform a crawl of a given URL."""
    logger = logging.getLogger(__name__)
    parameters = parameters or {}
    
    try:
        # Create crawler instance with parameters
        crawler = SimpleWebCrawler(
            max_pages=parameters.get("max_pages", 10),
            max_depth=parameters.get("max_depth", 3)
        )
        
        # Execute the crawl
        try:
            result = await crawler.crawl(url, parameters)
            return result
        except Exception as e:
            logger.error(f"Error during crawler execution: {str(e)}")
            # Create a valid CrawlResult on error
            return CrawlResult(
                status="error",
                results=[],
                url=url,
                message=str(e)
            )
            
    except Exception as e:
        logger.error(f"Error during crawl of {url}: {str(e)}")
        # Create a valid CrawlResult on error
        return CrawlResult(
            status="error",
            results=[],
            url=url,
            message=str(e)
        )

# Create a default crawler instance
crawler = SimpleWebCrawler()

# Async helper function to run crawler jobs
async def run_crawler_task(url, keywords=None, max_depth=2, max_pages=10):
    """Run a crawler task asynchronously."""
    parameters = {
        "max_depth": max_depth,
        "max_pages": max_pages,
        "keywords": keywords
    }
    try:
        result = await perform_crawl(url, parameters)
        return {
            "status": "success",
            "url": url,
            "pages_crawled": len(result.pages),
            "results": [{
                "url": page.url,
                "title": page.page_metadata.title,
                "content": page.content,
                "content_type": "text/markdown",
                "metadata": {
                    "crawled_at": page.page_metadata.last_fetched,
                    "depth": 0,  # We don't track depth per page with the new implementation
                    "links": [],  # Links are not stored per page in the new implementation
                    "description": page.page_metadata.description,
                    "language": page.page_metadata.language
                }
            } for page in result.pages]
        }
    except Exception as e:
        logging.error(f"Error during crawl of {url}: {str(e)}")
        return {
            "status": "error",
            "url": url,
            "message": str(e),
            "results": []
        }

# Helper for running multiple crawl jobs
async def run_multiple_crawler_tasks(urls, keywords=None, max_depth=1, max_pages=5):
    """Run multiple crawler tasks."""
    all_results = []
    successful_sites = 0
    
    for url in urls:
        try:
            result = await run_crawler_task(
                url=url,
                keywords=keywords,
                max_depth=max_depth,
                max_pages=max_pages
            )
            
            if result.get("status") == "success":
                successful_sites += 1
            
            all_results.append(result)
        except Exception as e:
            logging.error(f"Error during crawl of {url}: {str(e)}")
            all_results.append({
                "status": "error",
                "url": url,
                "message": str(e),
                "results": []
            })
    
    return {
        "status": "success" if successful_sites > 0 else "error",
        "successful_sites": successful_sites,
        "failed_sites": len(urls) - successful_sites,
        "crawl_results": all_results
    }

# Wrapper functions that work in both async and non-async contexts
def crawl_url(url, keywords=None, max_depth=2, max_pages=10):
    """Crawl a URL - wrapper that handles both async and non-async contexts."""
    return run_crawler_task(url, keywords, max_depth, max_pages)

def crawl_multiple_urls(urls, keywords=None, max_depth=1, max_pages=5):
    """Crawl multiple URLs - wrapper that handles both async and non-async contexts."""
    return run_multiple_crawler_tasks(urls, keywords, max_depth, max_pages) 