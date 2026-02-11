"""
ConfluencePublisher - Publishes to real Confluence server via REST API
"""
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from src.domain.core.publishing.contracts.publisher_contract import PublisherContract
from src.domain.core.rendering.dtos.rendered_document_dto import RenderedDocumentDTO
from src.domain.core.publishing.dtos.publish_target_dto import PublishTargetDTO
from src.domain.core.publishing.dtos.publish_result_dto import PublishResultDTO
from src.infrastructure.config.config import config
from src.domain.utils.example_generator_utils import ExampleGeneratorUtils


class ConfluencePublisher(PublisherContract):
    """Publisher that creates real pages in Confluence"""

    def __init__(self):
        """Initialize with Confluence configuration"""
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
                    # Create tag folder with unique prefix
                    tag_folder_title = f"{api_prefix} {tag.name.capitalize()}"
                    print(f"   📁 Creating tag folder: {tag_folder_title}...")
                    
                    tag_folder_content = self._generate_tag_folder_content(tag)

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
                    endpoint_count = 0
                    for path, path_item in api_spec.paths.items():
                        for method, operation in path_item.operations.items():
                            if tag.name in operation.tags:
                                endpoint_count += 1
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

            # 4. Create Data Models page if schemas exist
            if api_spec.components and api_spec.components.schemas:
                print(f"\n📊 Creating Data Models page...")
                models_title = f"{api_prefix} Data Models"
                models_content = self._generate_models_content(api_spec, api_prefix)

                # Save models content
                generated_contents['models'] = (models_title, models_content)

                models_page = self._create_or_update_page(
                    title=models_title,
                    content=models_content,
                    parent_id=root_id,
                    labels=['schemas', 'models']
                )

                if models_page:
                    models_url = f"{self.base_url}/spaces/{self.space_key}/pages/{models_page['id']}"
                    created_pages['models'] = models_url
                    print(f"✅ Created: {models_title}")

            # 5. Create Security page if security schemes exist
            if api_spec.components and api_spec.components.security_schemes:
                print(f"\n🔐 Creating Security page...")
                security_title = f"{api_prefix} Security"
                security_content = self._generate_security_content(api_spec)

                # Save security content
                generated_contents['security'] = (security_title, security_content)

                security_page = self._create_or_update_page(
                    title=security_title,
                    content=security_content,
                    parent_id=root_id,
                    labels=['security', 'authentication']
                )

                if security_page:
                    security_url = f"{self.base_url}/spaces/{self.space_key}/pages/{security_page['id']}"
                    created_pages['security'] = security_url
                    print(f"✅ Created: {security_title}")

            # Success
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
        """Generate rich overview content for root page with centered layout"""
        version = api_spec.info.version
        description = api_spec.info.description or "API Documentation"

        # Count endpoints
        endpoint_count = sum(len(path.operations) for path in api_spec.paths.values())

        # Server URLs
        servers_html = ""
        if api_spec.servers:
            servers_html = "<ul>"
            for server in api_spec.servers:
                desc = f" - {server.description}" if server.description else ""
                servers_html += f"<li><code>{server.url}</code>{desc}</li>"
            servers_html += "</ul>"

        content = f"""<h1>{title}</h1>
<p><strong>Version:</strong> {version}</p>

<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:rich-text-body>
    <p>{description}</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>📋 API Summary</h2>
<table>
  <tr>
    <th>Property</th>
    <th>Value</th>
  </tr>
  <tr>
    <td><strong>Title</strong></td>
    <td>{title}</td>
  </tr>
  <tr>
    <td><strong>Version</strong></td>
    <td>{version}</td>
  </tr>
  <tr>
    <td><strong>OpenAPI Version</strong></td>
    <td>{api_spec.openapi_version}</td>
  </tr>
  <tr>
    <td><strong>Total Endpoints</strong></td>
    <td>{endpoint_count}</td>
  </tr>
  <tr>
    <td><strong>Tags</strong></td>
    <td>{len(api_spec.tags)}</td>
  </tr>
</table>

<h2>🌐 Base URLs</h2>
{servers_html if servers_html else "<p>No servers defined</p>"}

<h2>📚 Documentation Structure</h2>
<p>This documentation is organized into the following child pages:</p>

<ac:structured-macro ac:name="children" ac:schema-version="2">
  <ac:parameter ac:name="all">true</ac:parameter>
  <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<h2>🏷️ Available Tags</h2>
<ul>
{"".join(f'<li><strong>{tag.name}</strong>{" - " + tag.description if tag.description else ""}</li>' for tag in api_spec.tags)}
</ul>

<p><em>Documentation generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
"""
        return content

    def _generate_tag_content(self, api_spec, tag) -> str:
        """Generate content for a tag page with actual endpoints"""
        tag_name = tag.name
        tag_description = tag.description or f"Endpoints for {tag_name}"

        # Find all endpoints with this tag
        endpoints_html = ""
        for path, path_item in api_spec.paths.items():
            for method, operation in path_item.operations.items():
                if tag_name in operation.tags:
                    # Generate endpoint documentation
                    summary = operation.summary or ""
                    description = operation.description or ""

                    # Method badge color
                    method_colors = {
                        'get': '#61affe',
                        'post': '#49cc90',
                        'put': '#fca130',
                        'delete': '#f93e3e',
                        'patch': '#50e3c2'
                    }
                    color = method_colors.get(method.lower(), '#999')

                    endpoints_html += f"""
<h3><ac:structured-macro ac:name="status" ac:schema-version="1">
  <ac:parameter ac:name="colour">{'Green' if method.lower() == 'get' else 'Blue'}</ac:parameter>
  <ac:parameter ac:name="title">{method.upper()}</ac:parameter>
</ac:structured-macro> {path}</h3>

<p><strong>{summary}</strong></p>
{f'<p>{description}</p>' if description else ''}
"""

                    # Parameters
                    if operation.parameters:
                        endpoints_html += "<h4>Parameters</h4><table><tr><th>Name</th><th>In</th><th>Type</th><th>Required</th><th>Description</th></tr>"
                        for param in operation.parameters:
                            # Extract type or schema reference
                            param_type = "string"  # default
                            if param.schema:
                                # Check if it's a reference to a model
                                if hasattr(param.schema, 'ref') and param.schema.ref:
                                    # Extract model name from $ref
                                    model_name = param.schema.ref.split('/')[-1]
                                    # Create link to Data Models page
                                    param_type = f'<ac:link><ri:page ri:content-title="Data Models"/><ac:plain-text-link-body><![CDATA[{model_name}]]></ac:plain-text-link-body></ac:link>'
                                elif param.schema.type:
                                    param_type = param.schema.type

                            required = "✅" if param.required else "❌"
                            param_desc = param.description or "-"
                            endpoints_html += f"<tr><td><code>{param.name}</code></td><td>{param.location}</td><td>{param_type}</td><td>{required}</td><td>{param_desc}</td></tr>"
                        endpoints_html += "</table>"

                    # Request Body
                    if operation.request_body:
                        endpoints_html += "<h4>Request Body</h4>"
                        endpoints_html += "<table><tr><th>Content Type</th><th>Schema</th><th>Required</th></tr>"

                        for content_type, media_obj in operation.request_body.content.items():
                            required_badge = "✅" if operation.request_body.required else "❌"

                            # Try to extract schema reference
                            schema_info = "object"
                            if media_obj.schema:
                                # Check if it's a reference to a model
                                if hasattr(media_obj.schema, 'ref') and media_obj.schema.ref:
                                    # Extract model name from $ref (e.g., "#/components/schemas/Pet" -> "Pet")
                                    model_name = media_obj.schema.ref.split('/')[-1]
                                    # Create link to Data Models page
                                    schema_info = f'<ac:link><ri:page ri:content-title="Data Models"/><ac:plain-text-link-body><![CDATA[{model_name}]]></ac:plain-text-link-body></ac:link>'
                                elif hasattr(media_obj.schema, 'type'):
                                    schema_info = media_obj.schema.type

                            endpoints_html += f"<tr><td><code>{content_type}</code></td><td>{schema_info}</td><td>{required_badge}</td></tr>"

                        endpoints_html += "</table>"

                        # Add description if exists
                        if operation.request_body.description:
                            endpoints_html += f"<p><em>{operation.request_body.description}</em></p>"

                    # Responses
                    if operation.responses:
                        endpoints_html += "<h4>Responses</h4><table><tr><th>Status</th><th>Description</th></tr>"
                        for status, response in operation.responses.items():
                            status_color = "Green" if status.startswith('2') else "Yellow" if status.startswith('4') else "Red"
                            endpoints_html += f'<tr><td><ac:structured-macro ac:name="status" ac:schema-version="1"><ac:parameter ac:name="colour">{status_color}</ac:parameter><ac:parameter ac:name="title">{status}</ac:parameter></ac:structured-macro></td><td>{response.description}</td></tr>'
                        endpoints_html += "</table>"

                    # cURL Example
                    curl_example = self._generate_curl_example(api_spec, path, method, operation)
                    # Escape HTML entities in curl example
                    curl_example_escaped = curl_example.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    endpoints_html += f"""
<h4>cURL Example</h4>
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[{curl_example_escaped}]]></ac:plain-text-body>
</ac:structured-macro>
"""

                    endpoints_html += "<hr/>"

        content = f"""
<h1>{tag_name}</h1>

<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:rich-text-body>
    <p>{tag_description}</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>🔌 Endpoints</h2>
{endpoints_html if endpoints_html else '<p>No endpoints found for this tag.</p>'}
"""
        return content

    def _generate_tag_folder_content(self, tag) -> str:
        """Generate content for tag folder page (container for endpoints)"""
        tag_name = tag.name
        tag_description = tag.description or f"API endpoints for {tag_name} operations"

        content = f"""
<h1>{tag_name}</h1>

<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:rich-text-body>
    <p>{tag_description}</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>📋 Endpoints</h2>
<p>Browse the child pages below to view detailed documentation for each endpoint:</p>

<ac:structured-macro ac:name="children" ac:schema-version="2">
  <ac:parameter ac:name="all">true</ac:parameter>
  <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<h2>ℹ️ About</h2>
<p>Each endpoint page contains:</p>
<ul>
  <li>Request parameters and schemas</li>
  <li>Request body specifications</li>
  <li>Response codes and descriptions</li>
  <li>cURL examples for testing</li>
</ul>
"""
        return content

    def _generate_single_endpoint_content(
        self,
        api_spec,
        path: str,
        method: str,
        operation,
        api_prefix: str = ""
    ) -> str:
        """Generate content for a single endpoint page with consistent layout structure"""

        # Data Models page title with API prefix for correct linking
        data_models_title = f"{api_prefix} Data Models" if api_prefix else "Data Models"

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

        summary = operation.summary or f"{method.upper()} {path}"
        description = operation.description or ""

        # No wrapper div - let Confluence use native full-width layout
        content = f"""<h1><ac:structured-macro ac:name="status" ac:schema-version="1">
  <ac:parameter ac:name="colour">{method_color}</ac:parameter>
  <ac:parameter ac:name="title">{method.upper()}</ac:parameter>
</ac:structured-macro> {path}</h1>

<p><strong>{summary}</strong></p>
{f'<p>{description}</p>' if description else ''}

<hr/>
"""

        # Parameters Section
        content += self._generate_parameters_section(operation, data_models_title)

        # Request Body Section
        content += self._generate_request_body_section(operation, data_models_title, example_generator)

        # Responses Section
        content += self._generate_responses_section(operation, example_generator)

        # cURL Example Section
        content += self._generate_curl_section(api_spec, path, method, operation)


        return content

    def _generate_parameters_section(self, operation, data_models_title: str) -> str:
        """Generate parameters section with consistent structure"""
        if not operation.parameters:
            return ""

        content = "<h2>Parameters</h2>\n"
        content += '<table><colgroup><col style="width: 20%;"/><col style="width: 15%;"/><col style="width: 20%;"/><col style="width: 10%;"/><col style="width: 35%;"/></colgroup>\n'
        content += "<tr><th>Name</th><th>In</th><th>Type</th><th>Required</th><th>Description</th></tr>\n"

        for param in operation.parameters:
            # Extract type or schema reference
            param_type = "string"
            if param.schema:
                if hasattr(param.schema, 'ref') and param.schema.ref:
                    model_name = param.schema.ref.split('/')[-1]
                    param_type = f'<ac:link><ri:page ri:content-title="{data_models_title}"/><ac:plain-text-link-body><![CDATA[{model_name}]]></ac:plain-text-link-body></ac:link>'
                elif param.schema.type:
                    param_type = param.schema.type

            required = "✅" if param.required else "❌"
            param_desc = param.description or "-"
            content += f"<tr><td><code>{param.name}</code></td><td>{param.location}</td><td>{param_type}</td><td>{required}</td><td>{param_desc}</td></tr>\n"

        content += "</table>\n<hr/>\n"
        return content

    def _generate_request_body_section(self, operation, data_models_title: str, example_generator) -> str:
        """Generate request body section with consistent structure"""
        if not operation.request_body:
            return ""

        content = "<h2>Request Body</h2>\n"
        content += '<table><colgroup><col style="width: 30%;"/><col style="width: 50%;"/><col style="width: 20%;"/></colgroup>\n'
        content += "<tr><th>Content Type</th><th>Schema</th><th>Required</th></tr>\n"

        for content_type, media_obj in operation.request_body.content.items():
            required_badge = "✅" if operation.request_body.required else "❌"

            schema_info = "object"
            if media_obj.schema:
                if hasattr(media_obj.schema, 'ref') and media_obj.schema.ref:
                    model_name = media_obj.schema.ref.split('/')[-1]
                    schema_info = f'<ac:link><ri:page ri:content-title="{data_models_title}"/><ac:plain-text-link-body><![CDATA[{model_name}]]></ac:plain-text-link-body></ac:link>'
                elif hasattr(media_obj.schema, 'type') and media_obj.schema.type == 'array':
                    # Handle array type with items reference
                    if media_obj.schema.items and hasattr(media_obj.schema.items, 'ref') and media_obj.schema.items.ref:
                        item_model_name = media_obj.schema.items.ref.split('/')[-1]
                        schema_info = f'array[<ac:link><ri:page ri:content-title="{data_models_title}"/><ac:plain-text-link-body><![CDATA[{item_model_name}]]></ac:plain-text-link-body></ac:link>]'
                    elif media_obj.schema.items and hasattr(media_obj.schema.items, 'type'):
                        schema_info = f'array[{media_obj.schema.items.type}]'
                    else:
                        schema_info = 'array[object]'
                elif hasattr(media_obj.schema, 'type'):
                    schema_info = media_obj.schema.type

            content += f"<tr><td><code>{content_type}</code></td><td>{schema_info}</td><td>{required_badge}</td></tr>\n"

        content += "</table>\n"

        if operation.request_body.description:
            content += f"<p><em>{operation.request_body.description}</em></p>\n"

        # Request Body JSON Example - EXACT SAME STRUCTURE AS RESPONSE (which works!)
        for content_type, media_obj in operation.request_body.content.items():
            if 'json' in content_type and media_obj.schema:
                example_json = ""
                if media_obj.example:
                    example_json = json.dumps(media_obj.example, indent=2, ensure_ascii=False)
                else:
                    example_json = example_generator.generate_example_json(media_obj.schema)

                # Skip empty JSON examples
                if example_json.strip() in ['{}', '""', 'null', '']:
                    continue

                # Escape for CDATA
                example_json_escaped = example_json.replace(']]>', ']]]]><![CDATA[>')

                # EXACT COPY of Response structure
                content += f"""<div style="margin-top: 12px;">
<p><strong>Request Body Example ({content_type}):</strong></p>
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">json</ac:parameter>
  <ac:plain-text-body><![CDATA[{example_json_escaped}]]></ac:plain-text-body>
</ac:structured-macro>
</div>
"""

        content += "<hr/>\n"
        return content

    def _generate_responses_section(self, operation, example_generator) -> str:
        """Generate responses section with consistent structure"""
        if not operation.responses:
            return ""

        content = "<h2>Responses</h2>\n"

        for status, response in operation.responses.items():
            status_color = "Green" if status.startswith('2') else "Yellow" if status.startswith('4') else "Red"
            content += f"""
<h3><ac:structured-macro ac:name="status" ac:schema-version="1">
  <ac:parameter ac:name="colour">{status_color}</ac:parameter>
  <ac:parameter ac:name="title">{status}</ac:parameter>
</ac:structured-macro> {response.description}</h3>
"""
            # Response Body Example
            if response.content:
                for content_type, media_obj in response.content.items():
                    if 'json' in content_type and media_obj.schema:
                        example_json = ""
                        if media_obj.example:
                            example_json = json.dumps(media_obj.example, indent=2, ensure_ascii=False)
                        else:
                            example_json = example_generator.generate_example_json(media_obj.schema)

                        # Skip empty JSON examples
                        if example_json.strip() in ['{}', '""', 'null', '']:
                            continue

                        # Escape for CDATA
                        example_json_escaped = example_json.replace(']]>', ']]]]><![CDATA[>')

                        content += f"""<div style="margin-top: 12px;">
<p><strong>Response Example ({content_type}):</strong></p>
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">json</ac:parameter>
  <ac:plain-text-body><![CDATA[{example_json_escaped}]]></ac:plain-text-body>
</ac:structured-macro>
</div>
"""

        content += "<hr/>\n"
        return content

    def _generate_curl_section(self, api_spec, path: str, method: str, operation) -> str:
        """Generate cURL example section"""
        curl_example = self._generate_curl_example(api_spec, path, method, operation)
        curl_example_escaped = curl_example.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        content = f"""
<h2>cURL Example</h2>
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[{curl_example_escaped}]]></ac:plain-text-body>
</ac:structured-macro>
"""

        return content

    def _generate_models_content(self, api_spec, api_prefix: str = "") -> str:
        """Generate content for Data Models page with schemas grouped by tag"""

        # Data Models page title with API prefix for internal links
        data_models_title = f"{api_prefix} Data Models" if api_prefix else "Data Models"

        # Build a map of which schemas are used by which tags
        tag_schemas = {}
        used_schemas = set()

        for tag in api_spec.tags:
            tag_schemas[tag.name] = set()

            # Find schemas used by this tag's endpoints
            for path, path_item in api_spec.paths.items():
                for method, operation in path_item.operations.items():
                    if tag.name in operation.tags:
                        # Check request body
                        if operation.request_body:
                            for content_type, media_obj in operation.request_body.content.items():
                                if media_obj.schema and hasattr(media_obj.schema, 'ref') and media_obj.schema.ref:
                                    model_name = media_obj.schema.ref.split('/')[-1]
                                    tag_schemas[tag.name].add(model_name)
                                    used_schemas.add(model_name)

                        # Check parameters
                        if operation.parameters:
                            for param in operation.parameters:
                                if param.schema and hasattr(param.schema, 'ref') and param.schema.ref:
                                    model_name = param.schema.ref.split('/')[-1]
                                    tag_schemas[tag.name].add(model_name)
                                    used_schemas.add(model_name)

        # Generate content with full width layout
        content = """<h1>Data Models</h1>

<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:rich-text-body>
    <p>Schema definitions and data structures used by the API, organized by endpoint categories.</p>
  </ac:rich-text-body>
</ac:structured-macro>
"""

        # Schemas grouped by tag
        if api_spec.components and api_spec.components.schemas:
            for tag in api_spec.tags:
                if tag.name in tag_schemas and len(tag_schemas[tag.name]) > 0:
                    content += f"<h2>{tag.name} Schemas</h2>"

                    for schema_name in sorted(tag_schemas[tag.name]):
                        if schema_name in api_spec.components.schemas:
                            schema = api_spec.components.schemas[schema_name]
                            schema_desc = schema.description or f"Schema definition for {schema_name}"

                            content += f"""
<h3 id="schema-{schema_name}">{schema_name}</h3>
<p>{schema_desc}</p>
"""

                            if schema.properties:
                                content += "<table><tr><th>Property</th><th>Type</th><th>Required</th><th>Description</th></tr>"
                                for prop_name, prop in schema.properties.items():
                                    prop_type = self._get_property_type_with_link(prop, data_models_title)
                                    is_required = "✅" if prop_name in (schema.required or []) else "❌"
                                    prop_desc = prop.description or "-"
                                    content += f"<tr><td><code>{prop_name}</code></td><td>{prop_type}</td><td>{is_required}</td><td>{prop_desc}</td></tr>"
                                content += "</table>"

                            content += "<hr/>"

            # Other schemas not associated with any tag
            other_schemas = [name for name in api_spec.components.schemas.keys() if name not in used_schemas]
            if other_schemas:
                content += "<h2>Other Schemas</h2>"

                for schema_name in sorted(other_schemas):
                    schema = api_spec.components.schemas[schema_name]
                    schema_desc = schema.description or f"Schema definition for {schema_name}"

                    content += f"""
<h3 id="schema-{schema_name}">{schema_name}</h3>
<p>{schema_desc}</p>
"""

                    if schema.properties:
                        content += "<table><tr><th>Property</th><th>Type</th><th>Required</th><th>Description</th></tr>"
                        for prop_name, prop in schema.properties.items():
                            prop_type = self._get_property_type_with_link(prop, data_models_title)
                            is_required = "✅" if prop_name in (schema.required or []) else "❌"
                            prop_desc = prop.description or "-"
                            content += f"<tr><td><code>{prop_name}</code></td><td>{prop_type}</td><td>{is_required}</td><td>{prop_desc}</td></tr>"
                        content += "</table>"

                    content += "<hr/>"

        return content

    def _get_property_type_with_link(self, prop, data_models_title: str = "Data Models") -> str:
        """Generate property type string with links for refs and arrays"""
        # Check if it's a direct reference
        if hasattr(prop, 'ref') and prop.ref:
            model_name = prop.ref.split('/')[-1]
            # Use anchor link to schema section within the same Data Models page
            return f'<ac:link ac:anchor="schema-{model_name}"><ri:page ri:content-title="{data_models_title}"/><ac:plain-text-link-body><![CDATA[{model_name}]]></ac:plain-text-link-body></ac:link>'

        # Check if it's an array
        if hasattr(prop, 'type') and prop.type == 'array':
            if prop.items:
                # Array with reference
                if hasattr(prop.items, 'ref') and prop.items.ref:
                    item_model_name = prop.items.ref.split('/')[-1]
                    # Use anchor link to schema section within the same Data Models page
                    return f'array[<ac:link ac:anchor="schema-{item_model_name}"><ri:page ri:content-title="{data_models_title}"/><ac:plain-text-link-body><![CDATA[{item_model_name}]]></ac:plain-text-link-body></ac:link>]'
                # Array with type
                elif hasattr(prop.items, 'type') and prop.items.type:
                    return f'array[{prop.items.type}]'
            return 'array[object]'

        # Default: return type or object
        return prop.type or "object"

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
        """Generate content for Endpoints folder page with centered layout"""
        content = """<h1>Endpoints</h1>

<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:rich-text-body>
    <p>This section contains all API endpoints organized by resource type.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>📋 Endpoint Categories</h2>
<p>Browse the child pages below to view detailed endpoint documentation:</p>

<ac:structured-macro ac:name="children" ac:schema-version="2">
  <ac:parameter ac:name="all">true</ac:parameter>
  <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>

<h2>ℹ️ About</h2>
<p>Each category contains detailed information about:</p>
<ul>
  <li>Available operations (GET, POST, PUT, DELETE, etc.)</li>
  <li>Request parameters and body schemas</li>
  <li>Response formats and status codes</li>
  <li>Example requests and responses</li>
</ul>
"""
        return content

    def _generate_security_content(self, api_spec) -> str:
        """Generate content for Security page with centered layout"""
        security_html = ""

        if api_spec.components and api_spec.components.security_schemes:
            for scheme_name, scheme in api_spec.components.security_schemes.items():
                scheme_type = scheme.type or "unknown"
                scheme_desc = scheme.description or f"Security scheme: {scheme_name}"

                security_html += f"""
<h3>{scheme_name}</h3>
<p><strong>Type:</strong> {scheme_type}</p>
<p>{scheme_desc}</p>
<hr/>
"""

        content = f"""<h1>Security</h1>

<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:rich-text-body>
    <p>This page describes the authentication and authorization mechanisms used by the API.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>🔐 Security Schemes</h2>
{security_html if security_html else '<p>No security schemes defined.</p>'}

<h2>ℹ️ Implementation Notes</h2>
<p>Please refer to the API specification for detailed implementation guidelines and examples.</p>
"""
        return content

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





