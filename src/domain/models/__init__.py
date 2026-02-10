"""Domain models package"""
# Import base models first (no dependencies)
from src.domain.models.info_model import InfoModel, ContactModel, LicenseModel
from src.domain.models.server_model import ServerModel, ServerVariableModel
from src.domain.models.tag_model import TagModel
from src.domain.models.schema_model import SchemaModel
from src.domain.models.security_scheme_model import SecuritySchemeModel, OAuthFlowModel

# Import models that depend on schema
from src.domain.models.parameter_model import ParameterModel
from src.domain.models.request_body_model import RequestBodyModel, MediaTypeObjectModel
from src.domain.models.response_model import ResponseModel

# Import models that depend on parameter/request/response
from src.domain.models.operation_model import OperationModel

# Import models that depend on operation
from src.domain.models.path_item_model import PathItemModel

# Import root model last
from src.domain.models.api_specification_model import ApiSpecificationModel, ComponentsModel

__all__ = [
    'InfoModel', 'ContactModel', 'LicenseModel',
    'ServerModel', 'ServerVariableModel',
    'TagModel',
    'SchemaModel',
    'ParameterModel',
    'RequestBodyModel', 'MediaTypeObjectModel',
    'ResponseModel',
    'OperationModel',
    'PathItemModel',
    'SecuritySchemeModel', 'OAuthFlowModel',
    'ApiSpecificationModel', 'ComponentsModel'
]




