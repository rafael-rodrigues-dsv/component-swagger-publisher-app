"""
ConfluencePublisher - Publishes to real Confluence server via REST API
"""
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.domain.core.publishing.contracts.publisher_contract import PublisherContract
from src.domain.core.rendering.dtos.rendered_document_dto import RenderedDocumentDTO
from src.domain.core.publishing.dtos.publish_target_dto import PublishTargetDTO
from src.domain.core.publishing.dtos.publish_result_dto import PublishResultDTO
from src.infrastructure.config.config import config
from src.domain.utils.example_generator_utils import ExampleGeneratorUtils


class ConfluencePublisher(PublisherContract):
    """Publisher that creates real pages in Confluence"""

    def __init__(self):
        """Initialize with Confluence configuration and Jinja2 templates"""
        self.base_url = config.confluence_base_url
        self.username = config.confluence_username
        self.token = config.confluence_token
        self.space_key = config.confluence_space_key
        self.parent_page_id = config.confluence_parent_page_id

        # Confluence REST API endpoint
        self.api_url = f"{self.base_url}/rest/api/content"

        # Headers for authentication - Confluence Cloud uses Basic Auth with email:token
        import base64
        # Username should be email for Confluence Cloud
        email = self.username if '@' in self.username else f"{self.username}@example.com"
        auth_string = f"{email}:{self.token}"
        auth_bytes = auth_string.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')

        self.headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Initialize Jinja2 template engine for server templates
        # __file__ = .../src/domain/core/publishing/publishers/confluence_publisher.py
        # Go up 5 levels to project root, then into src/infrastructure/...
        project_root = Path(__file__).parent.parent.parent.parent.parent.parent  # Go to project root
        templates_dir = project_root / "src" / "infrastructure" / "repository" / "templates" / "confluence" / "server"
        self.jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))
        self.jinja_env.filters['tojson_pretty'] = lambda x: json.dumps(x, indent=2, ensure_ascii=False) if x else '{}'

    def publish(self, document: RenderedDocumentDTO, target: PublishTargetDTO) -> PublishResultDTO:
        """
        Publish documentation to real Confluence server with full structure

        Creates a hierarchical structure:
        - Root page (API Overview) with rich content
        - Child pages for each tag (endpoints grouped)
        - Child page for Data Models
        """
        start_time = datetime.now()
        warnings = []
        errors = []
        created_pages = {}

        try:
            # Extract API specification from metadata
            api_spec = document.metadata.get('api_spec')
            if not api_spec:
                errors.append("API specification not found in document metadata")
                return self._error_result(errors, start_time)

            api_title = target.title or api_spec.info.title
            api_version = api_spec.info.version

            # Extract major.minor version (e.g., "1.0.7" -> "1.0")
            version_parts = api_version.split('.')
            major_minor = '.'.join(version_parts[:2]) if len(version_parts) >= 2 else api_version

            print(f"🚀 Publishing to Confluence: {self.space_key}")
            print(f"📍 Base URL: {self.base_url}")

            # 1. Create or update root page with rich content
            # Check if title already contains "API" or version
            root_title = api_title
            if " API" not in root_title.upper():
                root_title = f"{root_title} API"
            if major_minor not in root_title:
                root_title = f"{root_title} {major_minor}"

            print(f"\n📄 Creating root page: {root_title}...")
            root_content = self._generate_overview_content(api_spec, root_title)
            root_page = self._create_or_update_page(
                title=root_title,
                content=root_content,
                parent_id=self.parent_page_id,
                labels=target.labels or []
            )

            if not root_page:
                errors.append("Failed to create root page")
                return self._error_result(errors, start_time)

            root_id = root_page['id']
            page_url = f"{self.base_url}/spaces/{self.space_key}/pages/{root_id}"
            created_pages['root'] = page_url
            print(f"✅ Root page created: {page_url}")

            # Create unique prefix for child pages to avoid title conflicts in same space
            # Confluence doesn't allow duplicate titles in same space, even with different parents
            # Use API name + version as prefix: [Swagger Petstore 1.0]
            if major_minor not in api_title:
                api_prefix = f"[{api_title} {major_minor}]"
            else:
                api_prefix = f"[{api_title}]"

            api_identifier = api_title  # Used only for internal references

            # 2. Create "Endpoints" folder page with unique prefix
            print(f"\n📁 Creating Endpoints folder...")
            endpoints_folder_title = f"{api_prefix} Endpoints"
            endpoints_folder_content = self._generate_endpoints_folder_content(api_spec)
            endpoints_folder = self._create_or_update_page(
                title=endpoints_folder_title,
                content=endpoints_folder_content,
                parent_id=root_id,
                labels=['endpoints']
            )

            if not endpoints_folder:
                warnings.append("Failed to create Endpoints folder")
                endpoints_folder_id = root_id  # Fallback to root
            else:
                endpoints_folder_id = endpoints_folder['id']
                endpoints_url = f"{self.base_url}/spaces/{self.space_key}/pages/{endpoints_folder_id}"
                created_pages['endpoints_folder'] = endpoints_url
                print(f"✅ Endpoints folder created")

            # Initialize dictionary to collect ALL generated contents
            generated_contents = {
                'root': (root_title, root_content),
                'endpoints_folder': (endpoints_folder_title, endpoints_folder_content),
            }

            # 3. Create hierarchy: Endpoints → Tag folders → Individual endpoints
            if api_spec.tags:
                print(f"\n🔌 Creating endpoint structure...")
                total_endpoints = 0
                
                for tag in api_spec.tags:
                    # Count endpoints for this tag first
                    endpoint_count = sum(
                        1 for path, path_item in api_spec.paths.items()
                        for method, operation in path_item.operations.items()
                        if tag.name in operation.tags
                    )

                    # Create tag folder with unique prefix
                    tag_folder_title = f"{api_prefix} {tag.name.capitalize()}"
                    print(f"   📁 Creating tag folder: {tag_folder_title}...")
                    
                    tag_folder_content = self._generate_tag_folder_content(tag, endpoint_count)

                    # Save tag folder content
                    generated_contents[f'tag_{tag.name}'] = (tag_folder_title, tag_folder_content)

                    tag_folder = self._create_or_update_page(
                        title=tag_folder_title,
                        content=tag_folder_content,
                        parent_id=endpoints_folder_id,
                        labels=[tag.name.lower(), 'tag']
                    )
                    
                    if not tag_folder:
                        warnings.append(f"Failed to create tag folder: {tag_folder_title}")
                        continue
                    
                    tag_folder_id = tag_folder['id']
                    tag_folder_url = f"{self.base_url}/spaces/{self.space_key}/pages/{tag_folder_id}"
                    created_pages[f'tag_folder_{tag.name}'] = tag_folder_url
                    print(f"   ✅ Tag folder created: {tag_folder_title}")
                    
                    # Create individual endpoint pages under this tag
                    for path, path_item in api_spec.paths.items():
                        for method, operation in path_item.operations.items():
                            if tag.name in operation.tags:
                                total_endpoints += 1
                                
                                # Generate endpoint title with unique prefix
                                endpoint_title = f"{api_prefix} {method.upper()} {path}"
                                print(f"      📄 Creating: {endpoint_title}...")
                                
                                endpoint_content = self._generate_single_endpoint_content(
                                    api_spec, path, method, operation, api_prefix
                                )
                                
                                # Save endpoint content
                                safe_endpoint_key = f"{tag.name}_{method}_{path}".replace('/', '_').replace('{', '').replace('}', '')
                                generated_contents[f'endpoint_{safe_endpoint_key}'] = (endpoint_title, endpoint_content)

                                endpoint_page = self._create_or_update_page(
                                    title=endpoint_title,
                                    content=endpoint_content,
                                    parent_id=tag_folder_id,
                                    labels=[tag.name.lower(), method.lower(), 'endpoint']
                                )
                                
                                if endpoint_page:
                                    endpoint_url = f"{self.base_url}/spaces/{self.space_key}/pages/{endpoint_page['id']}"
                                    created_pages[f'endpoint_{tag.name}_{method}_{path.replace("/", "_")}'] = endpoint_url
                                    print(f"      ✅ Created: {endpoint_title}")
                                else:
                                    warnings.append(f"Failed to create endpoint: {endpoint_title}")
                    
                    print(f"   ✅ {endpoint_count} endpoints created for {tag.name}")
                
                print(f"\n✅ Total: {total_endpoints} endpoint pages created")

            # Success - No separate Data Models or Security pages
            # Everything is inline in endpoints now
            duration = (datetime.now() - start_time).total_seconds()

            print(f"\n✅ Published {len(created_pages)} pages in {duration:.2f}s")

            # Save ALL generated Confluence Storage Format to files
            # generated_contents already has all pages collected during creation
            self._save_storage_format(api_spec, target, generated_contents)

            return PublishResultDTO(
                success=True,
                output_paths=created_pages,
                warnings=warnings,
                metadata={
                    'publisher': 'confluence',
                    'space': self.space_key,
                    'base_url': self.base_url,
                    'pages_created': len(created_pages)
                },
                url=created_pages.get('root'),
                duration_seconds=duration
            )

        except requests.exceptions.RequestException as e:
            errors.append(f"Confluence API error: {str(e)}")
            return self._error_result(errors, start_time)
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._error_result(errors, start_time)

    def _create_or_update_page(
        self,
        title: str,
        content: str,
        parent_id: Optional[str] = None,
        labels: List[str] = None
    ) -> Optional[Dict]:
        """Create a new page or update if exists with same title AND parent"""

        # Check if page already exists with this title AND parent
        existing_page = self._find_page_by_title(title, parent_id)

        if existing_page:
            # Update existing page
            print(f"   ↻ Updating existing page (ID: {existing_page['id']}, Parent: {parent_id})...")
            return self._update_page(existing_page['id'], title, content, existing_page['version']['number'])
        else:
            # Create new page
            print(f"   ➕ Creating NEW page (Title: '{title}', Parent: {parent_id})...")
            return self._create_page(title, content, parent_id, labels)

    def _create_page(
        self,
        title: str,
        content: str,
        parent_id: Optional[str] = None,
        labels: List[str] = None
    ) -> Optional[Dict]:
        """Create a new Confluence page"""

        data = {
            'type': 'page',
            'title': title,
            'space': {'key': self.space_key},
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }

        # Add parent page if specified
        if parent_id:
            data['ancestors'] = [{'id': parent_id}]

        # Add labels if specified - format them for Confluence
        if labels:
            # Confluence label rules:
            # - Cannot start with a number
            # - Cannot contain spaces or dots
            # - Must be alphanumeric with hyphens/underscores
            formatted_labels = []
            for label in labels:
                # Replace dots with hyphens, remove spaces
                formatted = label.replace('.', '-').replace(' ', '-').lower()
                # If starts with number, prefix with 'v'
                if formatted and formatted[0].isdigit():
                    formatted = 'v' + formatted
                # Keep only alphanumeric, hyphens, underscores
                formatted = ''.join(c for c in formatted if c.isalnum() or c in '-_')
                if formatted:
                    formatted_labels.append(formatted)

            if formatted_labels:
                data['metadata'] = {
                    'labels': [{'name': label} for label in formatted_labels]
                }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"   ❌ Error creating page: {response.status_code}")
                print(f"   Response: {response.text}")
                if response.status_code == 403:
                    print(f"   💡 Tip: 403 error usually means:")
                    print(f"      - API token is invalid or expired")
                    print(f"      - User doesn't have write permission on space '{self.space_key}'")
                    print(f"      - Generate new token at: https://id.atlassian.com/manage-profile/security/api-tokens")
                return None

        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return None

    def _update_page(self, page_id: str, title: str, content: str, version: int) -> Optional[Dict]:
        """Update an existing Confluence page"""

        data = {
            'type': 'page',
            'title': title,
            'version': {'number': version + 1},
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }

        try:
            response = requests.put(
                f"{self.api_url}/{page_id}",
                headers=self.headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"   ❌ Error updating page: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return None

    def _find_page_by_title(self, title: str, parent_id: Optional[str] = None) -> Optional[Dict]:
        """Find a page by title in the configured space, optionally filtered by parent"""

        try:
            params = {
                'spaceKey': self.space_key,
                'title': title,
                'expand': 'version,ancestors'
            }

            response = requests.get(
                self.api_url,
                headers=self.headers,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                results = response.json().get('results', [])

                # If no parent_id specified, return first result
                if not parent_id:
                    return results[0] if results else None

                # If parent_id is specified, filter results to match parent
                if results:
                    for page in results:
                        page_id = page.get('id')

                        # Get full page details to verify parent
                        try:
                            page_detail_response = requests.get(
                                f"{self.api_url}/{page_id}",
                                headers=self.headers,
                                params={'expand': 'ancestors'},
                                timeout=30
                            )

                            if page_detail_response.status_code == 200:
                                page_detail = page_detail_response.json()
                                ancestors = page_detail.get('ancestors', [])

                                # Check if the immediate parent (last ancestor) matches
                                if ancestors and len(ancestors) > 0:
                                    immediate_parent_id = ancestors[-1].get('id')
                                    if immediate_parent_id == parent_id:
                                        return page
                        except Exception:
                            # If detail fetch fails, skip this page
                            continue

                    # No page with matching parent found
                    return None

                return None
            else:
                return None

        except Exception:
            return None

    def _convert_html_to_storage_format(self, html: str) -> str:
        """
        Convert HTML to Confluence Storage Format

        For MVP, we'll do basic conversions. Full implementation would use
        a proper HTML to Confluence Storage Format converter.
        """
        # Basic conversions for common HTML tags
        storage = html

        # Extract content from <body> if present
        if '<body>' in storage:
            start = storage.find('<body>') + 6
            end = storage.find('</body>')
            if end > start:
                storage = storage[start:end]

        # Remove <html>, <head>, <style> tags
        storage = storage.replace('<html>', '').replace('</html>', '')
        storage = storage.replace('<head>', '').replace('</head>', '')

        # Remove inline styles for cleaner Confluence pages
        import re
        storage = re.sub(r'<style[^>]*>.*?</style>', '', storage, flags=re.DOTALL)
        storage = re.sub(r' style="[^"]*"', '', storage)
        storage = re.sub(r' class="[^"]*"', '', storage)
        storage = re.sub(r' onclick="[^"]*"', '', storage)

        # Convert divs to paragraphs for better Confluence rendering
        storage = storage.replace('<div>', '<p>').replace('</div>', '</p>')

        # Remove script tags
        storage = re.sub(r'<script[^>]*>.*?</script>', '', storage, flags=re.DOTALL)

        # Clean up multiple empty paragraphs
        storage = re.sub(r'(<p>\s*</p>)+', '', storage)

        return storage.strip()

    def _generate_overview_content(self, api_spec, title: str) -> str:
        """Generate rich overview content for root page using Jinja2 template"""
        template = self.jinja_env.get_template('root.html.j2')
        return template.render(api=api_spec, title=title)


    def _generate_tag_folder_content(self, tag, endpoint_count: int = 0) -> str:
        """Generate content for tag folder page using Jinja2 template"""
        template = self.jinja_env.get_template('tag_folder.html.j2')
        return template.render(tag=tag, endpoint_count=endpoint_count)

    def _generate_single_endpoint_content(
        self,
        api_spec,
        path: str,
        method: str,
        operation,
        api_prefix: str = ""
    ) -> str:
        """Generate content for a single endpoint page using Jinja2 template"""

        # Create example generator with available schemas
        schemas = {}
        if api_spec.components and api_spec.components.schemas:
            schemas = api_spec.components.schemas
        example_generator = ExampleGeneratorUtils(schemas)

        # Method color mapping
        method_colors = {
            'get': 'Blue',
            'post': 'Green',
            'put': 'Yellow',
            'delete': 'Red',
            'patch': 'Purple'
        }
        method_color = method_colors.get(method.lower(), 'Grey')

        # Render template
        template = self.jinja_env.get_template('endpoint.html.j2')
        content = template.render(
            api=api_spec,
            path=path,
            method=method,
            operation=operation,
            method_color=method_color,
            example_generator=example_generator
        )

        return content


    def _generate_curl_example(self, api_spec, path: str, method: str, operation) -> str:
        """Generate a cURL example for an endpoint"""
        # Get base URL
        base_url = "https://api.example.com"
        if api_spec.servers and len(api_spec.servers) > 0:
            base_url = api_spec.servers[0].url

        # Build the full URL with path parameters replaced
        full_url = f"{base_url}{path}"

        # Replace path parameters with example values
        if operation.parameters:
            for param in operation.parameters:
                if param.location == 'path':
                    # Replace {paramName} with example value
                    example_value = self._get_param_example(param)
                    full_url = full_url.replace(f"{{{param.name}}}", str(example_value))

        # Start building cURL command
        curl_lines = [f"curl -X {method.upper()} '{full_url}'"]

        # Add headers
        curl_lines.append("  -H 'Accept: application/json'")

        # Add Content-Type for methods that typically have body
        if method.lower() in ['post', 'put', 'patch']:
            curl_lines.append("  -H 'Content-Type: application/json'")

        # Add query parameters
        query_params = []
        if operation.parameters:
            for param in operation.parameters:
                if param.location == 'query':
                    example_value = self._get_param_example(param)
                    query_params.append(f"{param.name}={example_value}")

        if query_params:
            # Add query params to URL
            separator = '&' if '?' in full_url else '?'
            params_str = '&'.join(query_params)
            curl_lines[0] = f"curl -X {method.upper()} '{full_url}{separator}{params_str}'"

        # Add request body for POST/PUT/PATCH
        if method.lower() in ['post', 'put', 'patch']:
            if operation.request_body:
                body_example = self._generate_body_example(operation.request_body, api_spec)
                curl_lines.append(f"  -d '{body_example}'")
            else:
                # Generic example body
                curl_lines.append("  -d '{\"key\": \"value\"}'")

        # Join with line continuation (using backslash and newline)
        curl_command = " \\\n".join(curl_lines)

        return curl_command

    def _get_param_example(self, param) -> str:
        """Get example value for a parameter"""
        # Check if parameter has example
        if hasattr(param, 'example') and param.example:
            return param.example

        # Generate based on type
        if param.schema:
            param_type = param.schema.type
            if param_type == 'integer':
                return "123"
            elif param_type == 'boolean':
                return "true"
            elif param_type == 'array':
                return "value1,value2"

        # Default to a meaningful name-based example
        param_name_lower = param.name.lower()
        if 'id' in param_name_lower:
            return "123"
        elif 'name' in param_name_lower:
            return "example"
        elif 'status' in param_name_lower:
            return "active"
        elif 'limit' in param_name_lower:
            return "10"
        elif 'offset' in param_name_lower:
            return "0"

        return "value"

    def _generate_body_example(self, request_body, api_spec=None) -> str:
        """Generate example JSON body for request"""
        # Create example generator if schemas available
        schemas = {}
        if api_spec and api_spec.components and api_spec.components.schemas:
            schemas = api_spec.components.schemas
        example_generator = ExampleGeneratorUtils(schemas)

        # Try to generate from request body content
        for content_type, media_obj in request_body.content.items():
            if 'json' in content_type:
                if media_obj.example:
                    return json.dumps(media_obj.example, ensure_ascii=False)
                elif media_obj.schema:
                    return example_generator.generate_example_json(media_obj.schema, pretty=False)

        return '{"key": "value"}'

    def _generate_endpoints_folder_content(self, api_spec) -> str:
        """Generate content for endpoints folder page using Jinja2 template"""
        template = self.jinja_env.get_template('endpoints_folder.html.j2')
        return template.render(api=api_spec)


    def _error_result(self, errors: List[str], start_time: datetime) -> PublishResultDTO:
        """Create an error result"""
        duration = (datetime.now() - start_time).total_seconds()
        return PublishResultDTO(
            success=False,
            errors=errors,
            duration_seconds=duration
        )

    def get_publisher_type(self) -> str:
        """Get publisher type"""
        return "confluence"

    def validate_target(self, target: PublishTargetDTO) -> bool:
        """Validate target and Confluence configuration"""
        if not config.is_confluence_configured():
            return False
        if not target.title:
            return False
        return True

    def _save_storage_format(self, api_spec, target, generated_contents: dict):
        """Save generated Confluence Storage Format to files for review/backup"""
        from pathlib import Path

        # Determine output directory based on mode (server/preview)
        # Server mode = real Confluence publication
        base_output_dir = Path("output/publisher/confluence/server")

        # Use API title for folder name (sanitize)
        api_title = target.title or api_spec.info.title
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in api_title)
        safe_title = safe_title.replace(' ', '_')

        # Add timestamp to avoid overwriting
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        api_output_dir = base_output_dir / f"{safe_title}_{timestamp}"
        api_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n💾 Saving Confluence Storage Format...")
        print(f"   📂 Directory: {api_output_dir}")

        saved_files = []
        file_counter = 1

        # Save root page
        if 'root' in generated_contents:
            title, content = generated_contents['root']
            root_file = api_output_dir / f"{file_counter:02d}_root_overview.xml"
            with open(root_file, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Page Title: {title} -->\n")
                f.write(f"<!-- Type: Root Overview -->\n")
                f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n\n")
                f.write(content)
            print(f"   ✅ Saved: {root_file.name}")
            saved_files.append(f"- `{root_file.name}` - {title}")
            file_counter += 1

        # Save endpoints folder
        if 'endpoints_folder' in generated_contents:
            title, content = generated_contents['endpoints_folder']
            endpoints_file = api_output_dir / f"{file_counter:02d}_endpoints_folder.xml"
            with open(endpoints_file, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Page Title: {title} -->\n")
                f.write(f"<!-- Type: Folder -->\n")
                f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n\n")
                f.write(content)
            print(f"   ✅ Saved: {endpoints_file.name}")
            saved_files.append(f"- `{endpoints_file.name}` - {title}")
            file_counter += 1

        # Save tag folders
        tag_files = {k: v for k, v in generated_contents.items() if k.startswith('tag_')}
        if tag_files:
            tags_dir = api_output_dir / "tags"
            tags_dir.mkdir(exist_ok=True)
            print(f"   📁 Saving {len(tag_files)} tag folders...")

            for tag_key, (title, content) in sorted(tag_files.items()):
                tag_name = tag_key.replace('tag_', '')
                safe_tag_name = "".join(c if c.isalnum() or c == '_' else '_' for c in tag_name)
                tag_file = tags_dir / f"{safe_tag_name}_folder.xml"

                with open(tag_file, 'w', encoding='utf-8') as f:
                    f.write(f"<!-- Page Title: {title} -->\n")
                    f.write(f"<!-- Type: Tag Folder -->\n")
                    f.write(f"<!-- Tag: {tag_name} -->\n")
                    f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n\n")
                    f.write(content)

                saved_files.append(f"- `tags/{tag_file.name}` - {title}")

            print(f"      ✅ Saved {len(tag_files)} tag folders")

        # Save individual endpoints
        endpoint_files = {k: v for k, v in generated_contents.items() if k.startswith('endpoint_')}
        if endpoint_files:
            endpoints_dir = api_output_dir / "endpoints"
            endpoints_dir.mkdir(exist_ok=True)
            print(f"   📄 Saving {len(endpoint_files)} endpoint pages...")

            for endpoint_key, (title, content) in sorted(endpoint_files.items()):
                # Extract tag, method, path from key: endpoint_pet_post__pet
                endpoint_name = endpoint_key.replace('endpoint_', '')
                safe_endpoint_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in endpoint_name)
                endpoint_file = endpoints_dir / f"{safe_endpoint_name}.xml"

                with open(endpoint_file, 'w', encoding='utf-8') as f:
                    f.write(f"<!-- Page Title: {title} -->\n")
                    f.write(f"<!-- Type: Endpoint -->\n")
                    f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n\n")
                    f.write(content)

                saved_files.append(f"- `endpoints/{endpoint_file.name}` - {title}")

            print(f"      ✅ Saved {len(endpoint_files)} endpoint pages")

        # Save data models
        if 'models' in generated_contents:
            title, content = generated_contents['models']
            models_file = api_output_dir / f"{file_counter:02d}_data_models.xml"
            with open(models_file, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Page Title: {title} -->\n")
                f.write(f"<!-- Type: Data Models -->\n")
                f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n\n")
                f.write(content)
            print(f"   ✅ Saved: {models_file.name}")
            saved_files.append(f"- `{models_file.name}` - {title}")
            file_counter += 1

        # Save security
        if 'security' in generated_contents:
            title, content = generated_contents['security']
            security_file = api_output_dir / f"{file_counter:02d}_security.xml"
            with open(security_file, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Page Title: {title} -->\n")
                f.write(f"<!-- Type: Security -->\n")
                f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n\n")
                f.write(content)
            print(f"   ✅ Saved: {security_file.name}")
            saved_files.append(f"- `{security_file.name}` - {title}")

        # Save README
        readme_file = api_output_dir / "README.md"
        total_pages = len(generated_contents)

        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(f"# Confluence Storage Format - {api_title}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Mode:** Server (Real Confluence Publication)\n")
            f.write(f"**Total Pages:** {total_pages}\n\n")

            f.write(f"## 📊 Summary\n\n")
            f.write(f"- Root page: 1\n")
            f.write(f"- Endpoints folder: 1\n")
            f.write(f"- Tag folders: {len(tag_files)}\n")
            f.write(f"- Individual endpoints: {len(endpoint_files)}\n")
            f.write(f"- Data Models: {1 if 'models' in generated_contents else 0}\n")
            f.write(f"- Security: {1 if 'security' in generated_contents else 0}\n\n")

            f.write(f"## 📁 Structure\n\n")
            f.write(f"```\n")
            f.write(f"{api_output_dir.name}/\n")
            f.write(f"├── 01_root_overview.xml\n")
            f.write(f"├── 02_endpoints_folder.xml\n")
            if 'models' in generated_contents:
                f.write(f"├── {file_counter:02d}_data_models.xml\n")
            if 'security' in generated_contents:
                f.write(f"├── {file_counter+1:02d}_security.xml\n")
            if tag_files:
                f.write(f"├── tags/\n")
                for tag_key in sorted(tag_files.keys()):
                    tag_name = tag_key.replace('tag_', '')
                    f.write(f"│   └── {tag_name}_folder.xml\n")
            if endpoint_files:
                f.write(f"└── endpoints/\n")
                f.write(f"    └── ... {len(endpoint_files)} endpoint XML files\n")
            f.write(f"```\n\n")

            f.write(f"## 📄 Files\n\n")
            for file_desc in saved_files[:10]:  # First 10
                f.write(f"{file_desc}\n")
            if len(saved_files) > 10:
                f.write(f"... and {len(saved_files) - 10} more files\n")

            f.write(f"\n## About\n\n")
            f.write(f"These XML files contain the Confluence Storage Format that was generated and published.\n\n")
            f.write(f"**Each XML file represents ONE page** published to Confluence.\n\n")
            f.write(f"You can use them to:\n\n")
            f.write(f"- Review the exact HTML structure sent to Confluence\n")
            f.write(f"- Debug layout issues on specific pages\n")
            f.write(f"- Manually copy/paste into Confluence if needed\n")
            f.write(f"- Backup of the complete documentation\n")
            f.write(f"- Compare versions over time\n")
            f.write(f"\n## Confluence Space\n\n")
            f.write(f"- **Space Key:** {self.space_key}\n")
            f.write(f"- **Base URL:** {self.base_url}\n")

        print(f"   ✅ Saved: {readme_file.name}")
        print(f"\n📍 Storage Format saved to: {api_output_dir.absolute()}")
        print(f"📊 Total files saved: {len(saved_files)}")





