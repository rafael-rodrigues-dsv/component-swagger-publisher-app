"""
ExampleGenerator - Generate JSON examples from OpenAPI schemas
"""
import json
from typing import Any, Dict, Optional
from src.domain.core.models.schema import Schema


class ExampleGenerator:
    """Generate JSON examples from OpenAPI schemas"""

    def __init__(self, schemas: Dict[str, Schema] = None):
        """Initialize with available schemas for resolving $ref"""
        self.schemas = schemas or {}
        self._visited_refs = set()  # Prevent infinite recursion

    def generate_example(self, schema: Schema) -> Any:
        """Generate an example value from a schema"""
        if schema is None:
            return {}

        # If schema has explicit example, use it
        if schema.example is not None:
            return schema.example

        # If it's a reference, resolve it
        if schema.ref:
            return self._resolve_ref(schema.ref)

        # Generate based on type
        schema_type = schema.type or 'object'

        if schema_type == 'object':
            return self._generate_object_example(schema)
        elif schema_type == 'array':
            return self._generate_array_example(schema)
        elif schema_type == 'string':
            return self._generate_string_example(schema)
        elif schema_type == 'integer':
            return self._generate_integer_example(schema)
        elif schema_type == 'number':
            return self._generate_number_example(schema)
        elif schema_type == 'boolean':
            return True
        else:
            return {}

    def generate_example_json(self, schema: Schema, pretty: bool = True) -> str:
        """Generate example as JSON string"""
        example = self.generate_example(schema)
        if pretty:
            return json.dumps(example, indent=2, ensure_ascii=False)
        return json.dumps(example, ensure_ascii=False)

    def _resolve_ref(self, ref: str) -> Any:
        """Resolve a $ref and generate example"""
        # Prevent infinite recursion
        if ref in self._visited_refs:
            return {"$ref": "circular reference"}

        self._visited_refs.add(ref)

        # Extract model name from ref (e.g., "#/components/schemas/Pet" -> "Pet")
        model_name = ref.split('/')[-1]

        if model_name in self.schemas:
            schema = self.schemas[model_name]
            result = self.generate_example(schema)
            self._visited_refs.discard(ref)
            return result

        self._visited_refs.discard(ref)
        return {}

    def _generate_object_example(self, schema: Schema) -> Dict[str, Any]:
        """Generate example for object type"""
        result = {}

        if schema.properties:
            for prop_name, prop_schema in schema.properties.items():
                result[prop_name] = self.generate_example(prop_schema)

        return result

    def _generate_array_example(self, schema: Schema) -> list:
        """Generate example for array type"""
        if schema.items:
            return [self.generate_example(schema.items)]
        return []

    def _generate_string_example(self, schema: Schema) -> str:
        """Generate example for string type"""
        # Use enum if available
        if schema.enum:
            return schema.enum[0]

        # Use default if available
        if schema.default is not None:
            return schema.default

        # Generate based on format
        if schema.format:
            format_examples = {
                'date': '2026-02-09',
                'date-time': '2026-02-09T18:45:05.992Z',
                'email': 'user@example.com',
                'uri': 'https://example.com',
                'url': 'https://example.com',
                'uuid': '550e8400-e29b-41d4-a716-446655440000',
                'password': '********',
                'byte': 'dGVzdA==',
                'binary': 'binary data',
                'hostname': 'example.com',
                'ipv4': '192.168.1.1',
                'ipv6': '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
            }
            return format_examples.get(schema.format, 'string')

        return 'string'

    def _generate_integer_example(self, schema: Schema) -> int:
        """Generate example for integer type"""
        # Use enum if available
        if schema.enum:
            return schema.enum[0]

        # Use default if available
        if schema.default is not None:
            return schema.default

        # Use minimum/maximum hints
        if schema.minimum is not None:
            return int(schema.minimum)
        if schema.maximum is not None:
            return int(schema.maximum) - 1

        return 0

    def _generate_number_example(self, schema: Schema) -> float:
        """Generate example for number type"""
        # Use enum if available
        if schema.enum:
            return schema.enum[0]

        # Use default if available
        if schema.default is not None:
            return schema.default

        # Use minimum/maximum hints
        if schema.minimum is not None:
            return float(schema.minimum)
        if schema.maximum is not None:
            return float(schema.maximum) - 0.1

        return 0.0




