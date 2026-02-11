"""
DomainMapperUtils - Convert ParsedSpec to ApiSpecification
"""
from typing import Dict, Any, List
from src.domain.core.parsing import ParsedSpecDTO
from src.domain.models.api_specification_model import ApiSpecificationModel, ComponentsModel
from src.domain.models.info_model import InfoModel, ContactModel, LicenseModel
from src.domain.models.server_model import ServerModel, ServerVariableModel
from src.domain.models.tag_model import TagModel
from src.domain.models.path_item_model import PathItemModel
from src.domain.models.operation_model import OperationModel
from src.domain.models.parameter_model import ParameterModel
from src.domain.models.request_body_model import RequestBodyModel, MediaTypeObjectModel
from src.domain.models.response_model import ResponseModel
from src.domain.models.schema_model import SchemaModel
from src.domain.models.security_scheme_model import SecuritySchemeModel, OAuthFlowModel


class DomainMapperUtils:
    """Map ParsedSpec to domain ApiSpecificationModel"""

    @staticmethod
    def to_domain(parsed_spec: ParsedSpecDTO) -> ApiSpecificationModel:
        """Convert ParsedSpec to ApiSpecificationModel"""
        raw = parsed_spec.raw_dict
        version = parsed_spec.version

        # Map Info
        info = DomainMapperUtils._map_info(raw.get('info', {}))

        # Map Servers
        servers = DomainMapperUtils._map_servers(raw, version)

        # Map Tags
        tags = DomainMapperUtils._map_tags(raw.get('tags', []))

        # Map Paths
        paths = DomainMapperUtils._map_paths(raw.get('paths', {}))

        # Map Components
        components = DomainMapperUtils._map_components(raw, version)

        # Security
        security = raw.get('security')

        return ApiSpecificationModel(
            openapi_version=version,
            info=info,
            servers=servers,
            paths=paths,
            components=components,
            tags=tags,
            security=security,
            external_docs=raw.get('externalDocs')
        )

    @staticmethod
    def _map_info(info_dict: Dict[str, Any]) -> InfoModel:
        """Map info section"""
        contact_dict = info_dict.get('contact', {})
        contact = ContactModel(
            name=contact_dict.get('name'),
            url=contact_dict.get('url'),
            email=contact_dict.get('email')
        ) if contact_dict else None

        license_dict = info_dict.get('license', {})
        license_obj = LicenseModel(
            name=license_dict.get('name', ''),
            url=license_dict.get('url')
        ) if license_dict else None

        return InfoModel(
            title=info_dict.get('title', 'Untitled API'),
            version=info_dict.get('version', '1.0.0'),
            description=info_dict.get('description'),
            terms_of_service=info_dict.get('termsOfService'),
            contact=contact,
            license=license_obj
        )

    @staticmethod
    def _map_servers(raw: Dict[str, Any], version: str) -> List[ServerModel]:
        """Map servers section"""
        servers = []

        # OpenAPI 3.x has servers array
        if 'servers' in raw:
            for server_dict in raw['servers']:
                variables = {}
                for var_name, var_dict in server_dict.get('variables', {}).items():
                    variables[var_name] = ServerVariableModel(
                        default=var_dict.get('default', ''),
                        enum=var_dict.get('enum'),
                        description=var_dict.get('description')
                    )

                servers.append(ServerModel(
                    url=server_dict.get('url', ''),
                    description=server_dict.get('description'),
                    variables=variables
                ))

        # Swagger 2.0 uses host, basePath, schemes
        elif version.startswith('2.'):
            host = raw.get('host', 'localhost')
            base_path = raw.get('basePath', '/')
            schemes = raw.get('schemes', ['https'])

            for scheme in schemes:
                url = f"{scheme}://{host}{base_path}"
                servers.append(ServerModel(url=url))

        return servers

    @staticmethod
    def _map_tags(tags_list: List[Dict[str, Any]]) -> List[TagModel]:
        """Map tags"""
        tags = []
        for tag_dict in tags_list:
            tags.append(TagModel(
                name=tag_dict.get('name', ''),
                description=tag_dict.get('description'),
                external_docs=tag_dict.get('externalDocs')
            ))
        return tags

    @staticmethod
    def _map_paths(paths_dict: Dict[str, Any]) -> Dict[str, PathItemModel]:
        """Map paths"""
        paths = {}
        for path, path_item_dict in paths_dict.items():
            operations = {}

            # Map operations
            for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']:
                if method in path_item_dict:
                    op_dict = path_item_dict[method]
                    operations[method.upper()] = DomainMapperUtils._map_operation(method.upper(), path, op_dict)

            # Common parameters
            parameters = [DomainMapperUtils._map_parameter(p) for p in path_item_dict.get('parameters', [])]

            paths[path] = PathItemModel(
                path=path,
                summary=path_item_dict.get('summary'),
                description=path_item_dict.get('description'),
                operations=operations,
                parameters=parameters
            )

        return paths

    @staticmethod
    def _map_operation(method: str, path: str, op_dict: Dict[str, Any]) -> OperationModel:
        """Map operation"""
        # Parameters - filter out invalid ones
        parameters = []
        body_param = None  # For Swagger 2.0

        for p in op_dict.get('parameters', []):
            try:
                # Check for Swagger 2.0 body parameter
                if p.get('in') == 'body':
                    body_param = p
                    continue  # Don't add to regular parameters

                param = DomainMapperUtils._map_parameter(p)
                # Only add if parameter has a valid name
                if param.name and param.name != 'unnamed_parameter':
                    parameters.append(param)
            except Exception as e:
                # Skip invalid parameters instead of failing the entire operation
                print(f"Warning: Skipping invalid parameter: {e}")
                continue

        # Request body - OpenAPI 3.0 style
        request_body = None
        if 'requestBody' in op_dict:
            try:
                request_body = DomainMapperUtils._map_request_body(op_dict['requestBody'])
            except Exception as e:
                print(f"Warning: Failed to map request body: {e}")
        # Swagger 2.0 style - body parameter
        elif body_param:
            try:
                request_body = DomainMapperUtils._map_swagger2_body_param(body_param)
            except Exception as e:
                print(f"Warning: Failed to map Swagger 2.0 body param: {e}")

        # Responses
        responses = {}
        for status, response_dict in op_dict.get('responses', {}).items():
            try:
                responses[status] = DomainMapperUtils._map_response(response_dict)
            except Exception as e:
                print(f"Warning: Skipping response {status}: {e}")
                continue

        return OperationModel(
            method=method,
            path=path,
            operation_id=op_dict.get('operationId'),
            summary=op_dict.get('summary'),
            description=op_dict.get('description'),
            tags=op_dict.get('tags', []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            deprecated=op_dict.get('deprecated', False),
            security=op_dict.get('security')
        )

    @staticmethod
    def _map_parameter(param_dict: Dict[str, Any]) -> ParameterModel:
        """Map parameter"""
        schema = None
        if 'schema' in param_dict:
            schema = DomainMapperUtils._map_schema(param_dict['schema'])

        return ParameterModel(
            name=param_dict.get('name', ''),
            location=param_dict.get('in', 'query'),
            description=param_dict.get('description'),
            required=param_dict.get('required', False),
            deprecated=param_dict.get('deprecated', False),
            schema=schema,
            example=param_dict.get('example')
        )

    @staticmethod
    def _map_request_body(rb_dict: Dict[str, Any]) -> RequestBodyModel:
        """Map request body"""
        content = {}
        for media_type, media_dict in rb_dict.get('content', {}).items():
            schema = DomainMapperUtils._map_schema(media_dict.get('schema', {})) if 'schema' in media_dict else None
            content[media_type] = MediaTypeObjectModel(
                schema=schema,
                example=media_dict.get('example'),
                examples=media_dict.get('examples', {})
            )

        return RequestBodyModel(
            description=rb_dict.get('description'),
            content=content,
            required=rb_dict.get('required', False)
        )

    @staticmethod
    def _map_swagger2_body_param(body_param: Dict[str, Any]) -> RequestBodyModel:
        """Map Swagger 2.0 body parameter to RequestBodyModel"""
        schema = None
        if 'schema' in body_param:
            schema = DomainMapperUtils._map_schema(body_param['schema'])

        # In Swagger 2.0, body is always application/json
        content = {
            'application/json': MediaTypeObjectModel(
                schema=schema,
                example=body_param.get('x-example') or body_param.get('example'),
                examples=body_param.get('x-examples', {})
            )
        }

        return RequestBodyModel(
            description=body_param.get('description'),
            content=content,
            required=body_param.get('required', False)
        )

    @staticmethod
    def _map_response(response_dict: Dict[str, Any]) -> ResponseModel:
        """Map response"""
        content = {}

        # OpenAPI 3.0 style - has content object
        if 'content' in response_dict:
            for media_type, media_dict in response_dict.get('content', {}).items():
                schema = DomainMapperUtils._map_schema(media_dict.get('schema', {})) if 'schema' in media_dict else None
                content[media_type] = MediaTypeObjectModel(
                    schema=schema,
                    example=media_dict.get('example'),
                    examples=media_dict.get('examples', {})
                )
        # Swagger 2.0 style - schema at root level
        elif 'schema' in response_dict:
            schema = DomainMapperUtils._map_schema(response_dict['schema'])
            content['application/json'] = MediaTypeObjectModel(
                schema=schema,
                example=response_dict.get('examples', {}).get('application/json'),
                examples=response_dict.get('examples', {})
            )

        return ResponseModel(
            description=response_dict.get('description', ''),
            content=content,
            headers=response_dict.get('headers', {})
        )

    @staticmethod
    def _map_schema(schema_dict: Dict[str, Any]) -> SchemaModel:
        """Map schema"""
        # Handle $ref
        if '$ref' in schema_dict:
            return SchemaModel(ref=schema_dict['$ref'])

        # Properties
        properties = {}
        for prop_name, prop_dict in schema_dict.get('properties', {}).items():
            properties[prop_name] = DomainMapperUtils._map_schema(prop_dict)

        # Items (for arrays)
        items = None
        if 'items' in schema_dict:
            items = DomainMapperUtils._map_schema(schema_dict['items'])

        # Composition
        all_of = [DomainMapperUtils._map_schema(s) for s in schema_dict.get('allOf', [])]
        one_of = [DomainMapperUtils._map_schema(s) for s in schema_dict.get('oneOf', [])]
        any_of = [DomainMapperUtils._map_schema(s) for s in schema_dict.get('anyOf', [])]

        return SchemaModel(
            type=schema_dict.get('type'),
            format=schema_dict.get('format'),
            title=schema_dict.get('title'),
            description=schema_dict.get('description'),
            enum=schema_dict.get('enum'),
            pattern=schema_dict.get('pattern'),
            min_length=schema_dict.get('minLength'),
            max_length=schema_dict.get('maxLength'),
            minimum=schema_dict.get('minimum'),
            maximum=schema_dict.get('maximum'),
            properties=properties,
            required=schema_dict.get('required', []),
            items=items,
            all_of=all_of if all_of else None,
            one_of=one_of if one_of else None,
            any_of=any_of if any_of else None,
            example=schema_dict.get('example'),
            default=schema_dict.get('default'),
            nullable=schema_dict.get('nullable', False),
            read_only=schema_dict.get('readOnly', False),
            write_only=schema_dict.get('writeOnly', False),
            deprecated=schema_dict.get('deprecated', False)
        )

    @staticmethod
    def _map_components(raw: Dict[str, Any], version: str) -> ComponentsModel:
        """Map components"""
        components_dict = raw.get('components', {}) if version.startswith('3.') else raw.get('definitions', {})

        # Schemas
        schemas = {}
        schema_source = components_dict.get('schemas', {}) if version.startswith('3.') else raw.get('definitions', {})
        for schema_name, schema_dict in schema_source.items():
            schemas[schema_name] = DomainMapperUtils._map_schema(schema_dict)

        # Security schemes
        security_schemes = {}
        sec_source = components_dict.get('securitySchemes', {}) if version.startswith('3.') else raw.get('securityDefinitions', {})
        for scheme_name, scheme_dict in sec_source.items():
            security_schemes[scheme_name] = DomainMapperUtils._map_security_scheme(scheme_dict)

        return ComponentsModel(
            schemas=schemas,
            security_schemes=security_schemes,
            responses=components_dict.get('responses', {}),
            parameters=components_dict.get('parameters', {}),
            examples=components_dict.get('examples', {}),
            request_bodies=components_dict.get('requestBodies', {}),
            headers=components_dict.get('headers', {})
        )

    @staticmethod
    def _map_security_scheme(scheme_dict: Dict[str, Any]) -> SecuritySchemeModel:
        """Map security scheme"""
        flows = None
        if 'flows' in scheme_dict:
            flows = {}
            for flow_name, flow_dict in scheme_dict['flows'].items():
                flows[flow_name] = OAuthFlowModel(
                    authorization_url=flow_dict.get('authorizationUrl'),
                    token_url=flow_dict.get('tokenUrl'),
                    refresh_url=flow_dict.get('refreshUrl'),
                    scopes=flow_dict.get('scopes', {})
                )

        return SecuritySchemeModel(
            type=scheme_dict.get('type', 'apiKey'),
            description=scheme_dict.get('description'),
            name=scheme_dict.get('name'),
            location=scheme_dict.get('in'),
            scheme=scheme_dict.get('scheme'),
            bearer_format=scheme_dict.get('bearerFormat'),
            flows=flows,
            open_id_connect_url=scheme_dict.get('openIdConnectUrl')
        )






