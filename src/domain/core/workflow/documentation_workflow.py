"""
DocumentationWorkflow - Define o fluxo completo de documentação
Parse → Map → Render → Publish
"""
from typing import Union
from src.domain.core.parsing import ParsedSpec
from src.domain.models.api_specification_model import ApiSpecificationModel
from src.domain.core.rendering.dtos.rendered_document import RenderedDocument
from src.domain.core.publishing import PublishResult
from src.domain.core.publishing import PublishTarget
from src.domain.core.rendering.dtos.render_options import RenderOptions
from src.domain.utils.domain_mapper_utils import DomainMapperUtils
from src.domain.core.parsing.parsers import ParserFactory
from src.domain.core.rendering.renderers.html_renderer import HtmlRenderer
from src.domain.core.publishing.publishers.publisher_factory import PublisherFactory


class DocumentationWorkflow:
    """
    Workflow completo de documentação de API

    Fluxo de execução:
    1. Parse: OpenAPI Spec (URL/File/Dict) → ParsedSpec (estrutura intermediária)
    2. Map: ParsedSpec → ApiSpecificationModel (modelo de domínio canônico)
    3. Render: ApiSpecificationModel → RenderedDocument (HTML)
    4. Publish: RenderedDocument → Output (Confluence/Local/etc)

    Este workflow orquestra todas as etapas do processo de geração de documentação,
    garantindo que cada etapa seja executada na ordem correta e com as dependências
    necessárias.
    """

    def __init__(self):
        """Initialize workflow with factories"""
        self.parser_factory = ParserFactory()
        self.publisher_factory = PublisherFactory()
        self.renderer = HtmlRenderer()

    def execute(
        self,
        source: Union[str, dict],
        publisher_type: str = 'confluence',
        mode: str = 'preview',
        target: PublishTarget = None,
        render_options: RenderOptions = None
    ) -> PublishResult:
        """
        Executa o workflow completo de documentação

        Args:
            source: URL, file path ou dict contendo a especificação OpenAPI
            publisher_type: Tipo de publicador ('confluence', etc)
            mode: 'preview' (local HTML) ou 'publish' (publicação real)
            target: Configuração de destino para publicação
            render_options: Opções de renderização (tema, exemplos, etc)

        Returns:
            PublishResult: Resultado da publicação com status e metadados

        Raises:
            Exception: Se alguma etapa do workflow falhar

        Example:
            >>> workflow = DocumentationWorkflow()
            >>> result = workflow.execute(
            ...     source='https://api.example.com/openapi.json',
            ...     publisher_type='confluence',
            ...     mode='preview'
            ... )
            >>> print(result.success)
            True
        """
        # Step 1: Parse OpenAPI Specification
        # Detecta a versão (Swagger 2.0 ou OpenAPI 3.x) e converte para estrutura intermediária
        parser = self.parser_factory.get_parser(source)
        parsed_spec: ParsedSpec = parser.parse(source)

        # Step 2: Map to Domain Model
        # Converte a estrutura intermediária para o modelo de domínio canônico
        # Isso normaliza todas as versões para uma única representação
        api_spec: ApiSpecificationModel = DomainMapperUtils.to_domain(parsed_spec)

        # Step 3: Render to HTML
        # Gera documentação HTML responsiva com exemplos e navegação
        if render_options is None:
            render_options = RenderOptions(
                theme='light',
                responsive=True,
                include_examples=True
            )
        rendered_doc: RenderedDocument = self.renderer.render(api_spec, render_options)

        # Step 4: Publish
        # Publica a documentação no destino escolhido (local ou Confluence)
        publisher = self.publisher_factory.get_publisher(publisher_type, mode)
        result: PublishResult = publisher.publish(rendered_doc, target)

        return result

    def parse_only(self, source: Union[str, dict]) -> ApiSpecificationModel:
        """
        Executa apenas as etapas de parsing e mapeamento

        Útil para validação ou análise de especificações sem gerar documentação

        Args:
            source: URL, file path ou dict contendo a especificação OpenAPI

        Returns:
            ApiSpecificationModel: Modelo de domínio da API
        """
        parser = self.parser_factory.get_parser(source)
        parsed_spec = parser.parse(source)
        api_spec = DomainMapperUtils.to_domain(parsed_spec)
        return api_spec

    def render_only(
        self,
        api_spec: ApiSpecificationModel,
        render_options: RenderOptions = None
    ) -> RenderedDocument:
        """
        Executa apenas a renderização de um modelo já parseado

        Útil para re-renderizar com diferentes opções sem re-parsear

        Args:
            api_spec: Modelo de domínio da API já parseado
            render_options: Opções de renderização

        Returns:
            RenderedDocument: Documento HTML renderizado
        """
        if render_options is None:
            render_options = RenderOptions()
        return self.renderer.render(api_spec, render_options)

