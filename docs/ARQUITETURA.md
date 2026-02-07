# Arquitetura do Publicador de Documentações OpenAPI

## Visão Geral

**Projeto**: Publicador automatizado de especificações OpenAPI/Swagger para plataformas de documentação colaborativa.

**Propósito**: Ler especificações OpenAPI (2.0 e 3.x) em JSON/YAML, mapear para um modelo de domínio canônico, renderizar documentação em formato proprietário (inicialmente Confluence Storage Format / XML) e publicar em plataformas colaborativas com suporte para extensão futura.

**Princípios Arquiteturais**:
- **Separação de Responsabilidades**: Camadas bem definidas (application, domain, infrastructure).
- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.
- **Extensibilidade**: Novos parsers, renderizadores e plataformas de publicação sem alterar o núcleo.
- **Testabilidade**: Interfaces e injeção de dependência facilitam testes unitários e de integração.
- **Rastreabilidade**: Logs estruturados e erros tipados em todas as etapas.

## Objetivos

### **MVP (Mínimo Viável) - Fase 1: Preview Local**
- ✅ Ler e validar especificações OpenAPI 2.0/3.x (JSON/YAML) de URLs ou arquivos locais.
- ✅ Mapear para um modelo canônico da especificação, independente da versão.
- ✅ Gerar **preview em HTML responsivo** com CSS inline.
- ✅ Salvar **Storage Format XML** (Confluence) localmente em `output/publisher/confluence/`.
- ✅ Extrair automaticamente: Título, Labels, Endpoints (auto-inference).
- ✅ Interface CLI **MÍNIMAL**: apenas URL + Publisher choice.
- ✅ Abrir preview em navegador automaticamente.

### **Fase 2: Publicação em Confluence (Futuro)**
- ⏳ Integração com API REST do Confluence.
- ⏳ Usar credenciais em `config/.env`.
- ⏳ Criar/atualizar páginas em Confluence.
- ⏳ Retornar URL da página publicada.
- ⏳ Idempotência: atualizar se página existe.

### **Fase 3+: Extensões**
- ⏳ Suporte para outras plataformas (GitHub Pages, Notion, SharePoint, etc.).
- ⏳ Themes customizáveis.
- ⏳ Internacionalização (i18n).
- ⏳ Validações e reports avançados.

---

## Diagrama de Sequência (Fluxo Console - Simplificado)

Exemplo de URL (Petstore): `https://petstore.swagger.io/v2/swagger.json`

```
┌─────────────┐
│   USUÁRIO   │
└──────┬──────┘
       │
       │ Inicia aplicação
       ▼
   ┌──────────────────────────────────────────────────┐
   │         CLI (main.py) - MINIMAL INPUT             │
   ├──────────────────────────────────────────────────┤
   │ 📍 URL da especificação OpenAPI:                 │
   │    > https://petstore.swagger.io/v2/swagger.json │
   │                                                   │
   │ 📍 Publisher (confluence):                       │
   │    > confluence                                  │
   │                                                   │
   │ Monta PublishRequest(url, publisher)             │
   └──────────────────────────────────────────────────┘
       │
       │ PublishRequest { url, publisher }
       ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  Orchestrator: PublishDocumentation(request)                 │
   │                                                               │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ 1️⃣  PARSING & VERSION DETECTION                       │  │
   │  │    ParserFactory.detect_version(url)                  │  │
   │  │    → Swagger2Parser ou OpenApi3Parser                 │  │
   │  │    ↓ ParsedSpec { version, raw dict, $refs }         │  │
   │  └────────────────────────────────────────────────────────┘  │
   │                                                               │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ 2️⃣  DOMAIN MAPPING                                    │  │
   │  │    DomainMapper.to_domain(ParsedSpec)                 │  │
   │  │    ↓ ApiSpecification (modelo canônico)               │  │
   │  └────────────────────────────────────────────────────────┘  │
   │                                                               │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ 3️⃣  NORMALIZATION & AUTO-INFERENCE                    │  │
   │  │    SpecificationNormalizer.normalize(spec)            │  │
   │  │    • Resolve $ref                                     │  │
   │  │    • Padroniza media types                            │  │
   │  │    • Preenche defaults                                │  │
   │  │    AutoTitleExtractor: title = api.info.title         │  │
   │  │    AutoLabelsExtractor: labels = [tags, version]      │  │
   │  │    ↓ ApiSpecification (normalizada) + Metadata        │  │
   │  └────────────────────────────────────────────────────────┘  │
   │                                                               │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ 4️⃣  HTML RENDERING (Preview)                          │  │
   │  │    ConfluenceHtmlRenderer.render(spec)                │  │
   │  │    • Carrega templates Jinja2 (index, ops, schemas)   │  │
   │  │    • Renderiza HTML + CSS inline (elegante/responsivo)│  │
   │  │    • Gera storage format XML (Confluence)             │  │
   │  │    ↓ RenderedDocument { HTML, XML, assets }          │  │
   │  └────────────────────────────────────────────────────────┘  │
   │                                                               │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ 5️⃣  SAVE PREVIEW                                      │  │
   │  │    PublisherFactory.get(publisher)                    │  │
   │  │    • ConfluencePublisher: save HTML preview local     │  │
   │  │    • output/publisher/confluence/preview.html         │  │
   │  │    • output/publisher/confluence/storage.xml          │  │
   │  │    ↓ PublishResult { success, paths, warnings }       │  │
   │  └────────────────────────────────────────────────────────┘  │
   │                                                               │
   │  ✅ Retorna PublishResult                                   │  │
   └──────────────────────────────────────────────────────────────┘
       │
       │ PublishResult
       ▼
   ┌─────────────────────────────────────────────────────┐
   │  CLI: Exibe Resultado                               │
   ├─────────────────────────────────────────────────────┤
   │  ✨ Sucesso!                                        │
   │  📄 Preview: output/publisher/confluence/index.html │
   │  📋 Storage: output/publisher/confluence/index.xml  │
   │  ⏱️  Tempo: 2.1s                                    │
   │                                                      │
   │  Abrir: start output/publisher/confluence/index.html│
   └─────────────────────────────────────────────────────┘
```

**Notas Importantes**:
- **Entrada mínima**: Apenas URL + Publisher (Confluence)
- **Auto-inference**: Título extraído de `info.title`, labels de `tags` + `version`
- **Preview local**: HTML renderizado em `output/publisher/confluence/`
- **Storage format**: XML (Confluence Storage Format) também salvo localmente
- **Visual elegante**: Templates Jinja2 geram HTML responsivo e bem estruturado
- **Estrutura de output**: `output/{publisher}/{publisher_type}/{files}`

---

## Diagrama de Pastas (Hierarquia Atualizado)

```
component-swagger-publisher-app/
│
├── 🔐 config/                               ← Configurações & Credenciais
│   ├── .env                                (Credenciais Confluence - NÃO COMMITAR)
│   ├── .env.example                        (Template de .env)
│   ├── AppConfig.py                        (Classe de configuração)
│   └── EnvLoader.py                        (Carregamento de variáveis)
│
├── 🎯 application/                          ← Orquestração (ENTRADA MINIMAL: URL + Publisher)
│   ├── services/
│   │   ├── PublishingService.py            (Coordena parse → map → render → save)
│   │   ├── ParsingService.py               (Seleciona parser por versão)
│   ├── RenderingService.py             (Coordena renderização e templates)
│   └── AutoInferenceService.py         (Extrai título, labels, endpoints auto)
│   │
│   ├── orchestrators/
│   │
│   └── __init__.py
│
├── 🧠 domain/                               ← Modelo Canônico & Interfaces (Lógica Pura)
│   ├── core/
│   │   ├── models/
│   │   │   ├── ApiSpecification.py         (Raiz: info, servers, paths, components)
│   │   │   ├── Info.py                     (Metadados: título, descrição, versão)
│   │   │   ├── Server.py                   (Endpoints: URL, variáveis)
│   │   │   ├── PathItem.py                 (Caminho: operações HTTP)
│   │   │   ├── Operation.py                (Operação: params, request/response)
│   │   │   ├── Parameter.py                (Parâmetro: nome, tipo, localização)
│   │   │   ├── RequestBody.py              (Corpo: conteúdo, schema)
│   │   │   ├── Response.py                 (Resposta: status, conteúdo, schema)
│   │   │   ├── Schema.py                   (Tipo: properties, constraints)
│   │   │   ├── Example.py                  (Exemplo: valor, media type)
│   │   │   ├── Tag.py                      (Marcador: agrupa operações)
│   │   │   └── SecurityScheme.py           (Segurança: API Key, OAuth2, etc.)
│   │   │
│   │   ├── value_objects/
│   │   │   ├── Version.py                  (Versão validada)
│   │   │   ├── MediaType.py                (MIME type normalizado)
│   │   │   ├── HttpMethod.py               (GET, POST, PUT, DELETE, PATCH)
│   │   │   ├── StatusCode.py               (200, 400, 500, etc.)
│   │   │   └── Reference.py                ($ref com resolução)
│   │   │
│   │   └── services/
│   │       ├── SpecificationNormalizer.py  (Resolve $ref, padroniza, defaults)
│   │       ├── SpecificationValidator.py   (Valida integridade e regras)
│   │       └── DomainMapper.py             (Converte ParsedSpec → ApiSpecification)
│   │
│   ├── ports/                              (Interfaces/Contratos - Portas Hexagonais)
│   │   ├── parsing/
│   │   │   ├── OpenApiParser.py            (Interface: parse(input) → ParsedSpec)
│   │   │   └── ParsedSpec.py               (DTO intermediária)
│   │   │
│   │   ├── rendering/
│   │   │   ├── DocumentationRenderer.py    (Interface: render → RenderedDocument)
│   │   │   ├── RenderOptions.py            (Opções: tema, locale, includes)
│   │   │   └── RenderedDocument.py         (DTO: HTML + XML + assets)
│   │   │
│   │   ├── publishing/
│   │   │   ├── Publisher.py                (Interface: save preview local)
│   │   │   ├── PublishTarget.py            (DTO: publisher type, output path)
│   │   │   └── PublishResult.py            (DTO: sucesso, paths, warnings)
│   │   │
│   │   ├── templating/
│   │   │   ├── TemplateRepository.py       (Interface: get_template, list)
│   │   │   └── Template.py                 (DTO: nome, content Jinja2)
│   │   │
│   │   ├── inference/
│   │   │   ├── TitleExtractor.py           (Interface: extrai título)
│   │   │   └── LabelsExtractor.py          (Interface: extrai labels)
│   │   │
│   │   ├── http/
│   │   │   ├── HttpClient.py               (Interface: GET, POST com timeout)
│   │   │   └── HttpException.py            (Exceção: HTTP errors)
│   │   │
│   │   └── logging/
│   │       └── Logger.py                   (Interface: info, warn, error com requestId)
│   │
│   └── utils/
│       ├── JsonLoader.py                   (Carrega JSON de URL/arquivo/string)
│       ├── RefResolver.py                  (Resolve $ref locais/remotos)
│       └── PathUtils.py                    (Manipula caminhos OpenAPI)
│
├── ⚙️ infrastructure/                       ← Implementações Concretas
│   ├── parsing/
│   │   ├── Swagger2Parser.py               (Implementa para OpenAPI 2.0)
│   │   ├── OpenApi3Parser.py               (Implementa para OpenAPI 3.x)
│   │   └── ParserFactory.py                (Seleciona parser por versão)
│   │
│   ├── rendering/
│   │   ├── HtmlRenderer.py                 (Renderiza HTML + CSS inline)
│   │   ├── ConfluenceXmlRenderer.py        (Renderiza Storage Format XML)
│   │   └── ConfluenceStorageFormat.py      (Utilities para XML válido)
│   │
│   ├── publishing/
│   │   ├── ConfluencePublisher.py          (Salva preview local + XML)
│   │   ├── PublisherFactory.py             (Seleciona publisher)
│   │   └── FileOutputManager.py            (Gerencia output/publisher/*)
│   │
│   ├── inference/
│   │   ├── AutoTitleExtractor.py           (Implementa TitleExtractor)
│   │   ├── AutoLabelsExtractor.py          (Implementa LabelsExtractor)
│   │   └── AutoEndpointsExtractor.py       (Extrai servidores e paths)
│   │
│   ├── templating/
│   │   └── FileSystemTemplateRepository.py (Implementa TemplateRepository)
│   │
│   ├── http/
│   │   ├── UrllibHttpClient.py             (Implementa HttpClient - urllib nativo)
│   │   └── HttpConnectionError.py          (Implementação específica de exceção)
│   │
│   └── logging/
│       └── StructuredJsonLogger.py         (Implementa Logger - JSON estruturado)
│
├── 📚 repository/                           ← Artefatos Estáticos
│   ├── templates/
│   │   ├── confluence/
│   │   │   ├── index.html.j2               (Página raiz: HTML responsivo)
│   │   │   ├── index.xml.j2                (Página raiz: Storage Format XML)
│   │   │   ├── operation.html.j2           (Operação: HTML com tabs, code)
│   │   │   ├── operation.xml.j2            (Operação: Storage Format)
│   │   │   ├── schema.html.j2              (Schema: HTML tabulado)
│   │   │   ├── schema.xml.j2               (Schema: Storage Format)
│   │   │   ├── examples.html.j2            (Exemplos: HTML com syntax highlight)
│   │   │   ├── examples.xml.j2             (Exemplos: Storage Format)
│   │   │   ├── base.html.j2                (Base layout HTML)
│   │   │   ├── base.xml.j2                 (Base layout XML)
│   │   │   ├── macros.html.j2              (Macros HTML: cards, tabs, etc.)
│   │   │   ├── macros.xml.j2               (Macros XML: Confluence-specific)
│   │   │   ├── styles.css                  (CSS inline para HTML)
│   │   │   └── theme-light.css             (Tema claro)
│   │   │
│   ├── schemas/
│   │   ├── openapi_2_schema.json           (Validação OpenAPI 2.0)
│   │   └── openapi_3_schema.json           (Validação OpenAPI 3.x)
│   │
│   ├── fixtures/
│   │   ├── openapi_2_petstore.json         (Fixture de teste: Swagger 2.0)
│   │   ├── openapi_3_petstore.json         (Fixture de teste: OpenAPI 3.x)
│   │   ├── openapi_3_complex.json          (Fixture de teste: features avançadas)
│   │   ├── openapi_2_simple.json           (Fixture de teste: mínimo viável)
│   │   └── ... (outras APIs de exemplo para testes)
│   │
│   └── config/
│       └── default_config.ini              (Configuração padrão - INI format)
│
├── 📄 tests/                                ← Testes
│   ├── unit/
│   │   ├── test_parsing/
│   │   ├── test_domain/
│   │   ├── test_rendering/
│   │   ├── test_inference/
│   │   └── test_publishing/
│   │
│   ├── integration/
│   │   ├── test_e2e_confluence.py
│   │   └── test_full_workflow.py
│   │
│   └── fixtures/
│       └── conftest.py
│
├── 🖥️ cli/                                  ← Entrada de Execução (MINIMAL)
│   ├── main.py                             (Ponto de entrada: URL + Publisher)
│   ├── prompts.py                          (Interação com usuário (MINIMAL))
│   └── config_loader.py                    (Carrega config)
│
├── 📖 docs/                                 ← Documentação
│   ├── README.md                           (Como usar)
│   ├── ARCHITECTURE.md                     (Este arquivo)
│   ├── API.md                              (Especificação DTOs/interfaces)
│   └── EXAMPLES.md                         (Exemplos end-to-end)
│
├── 📁 output/                               ← OUTPUT GERADO (raiz do projeto)
│   └── publisher/
│       ├── confluence/
│       │   ├── index.html                  (Preview HTML renderizado)
│       │   ├── index.xml                   (Confluence Storage Format XML)
│       │   ├── styles.css                  (CSS embarcado no HTML)
│       │   ├── assets/
│       │   │   ├── images/                 (Imagens extraídas/geradas)
│       │   │   ├── schemas/                (JSONs de schemas)
│       │   │   └── examples/               (Exemplos de código)
│       │   └── logs/
│       │       └── publish.log             (Log de processamento)
│       │
│       └── [future: github-pages, notion, sharepoint]/
│
└── interfaces/
    └── contracts.md                        (Especificação de portas)
```

**Legenda - MUDANÇAS PRINCIPAIS**:
- 🎯 **APPLICATION** (Azul): Entrada MINIMAL (URL + Publisher), **AutoInferenceService**
- 🧠 **DOMAIN** (Amarelo): Modelo canônico, **inferência interfaces** (TitleExtractor, LabelsExtractor)
- ⚙️ **INFRASTRUCTURE** (Roxo): **Extractors** auto (título, labels, endpoints), **HtmlRenderer** + **ConfluenceXmlRenderer**
- 📚 **REPOSITORY** (Verde): Templates **HTML/XML com CSS elegante e responsivo**
- 📁 **OUTPUT** (Destacado): `output/publisher/confluence/` com preview HTML + storage XML
- 🖥️ **CLI** (Verde): **SIMPLIFICADO** - apenas URL + Publisher choice
- 📄 **OUTROS** (Cinza): Testes incluindo **test_inference/**, documentação

---

## Configuração de Publicação (Confluence)

### **Credenciais e Variáveis de Ambiente**

As configurações de publicação no Confluence devem ser armazenadas em `config/.env`:

```
# config/.env
CONFLUENCE_BASE_URL=https://confluence.sua-empresa.com
CONFLUENCE_USERNAME=seu_usuario
CONFLUENCE_TOKEN=seu_token_api_aqui
CONFLUENCE_SPACE_KEY=DEV
CONFLUENCE_PARENT_PAGE_ID=12345  # Opcional
```

### **Como Usar**

1. **Criar arquivo `.env`**:
```bash
cp config/.env.example config/.env
```

2. **Preencher credenciais** (não commitar `.env` para Git):
```bash
# .gitignore
config/.env
```

3. **Carregar no código**:
```python
# infrastructure/config/EnvLoader.py
from dotenv import load_dotenv
import os

load_dotenv('config/.env')

CONFLUENCE_BASE_URL = os.getenv('CONFLUENCE_BASE_URL')
CONFLUENCE_TOKEN = os.getenv('CONFLUENCE_TOKEN')
# ... outras variáveis
```

### **Estrutura de Config**

```
config/
├── .env                          ← Credenciais (NÃO commitar)
├── .env.example                  ← Template para credenciais
├── AppConfig.py                  ← Classe de configuração
└── EnvLoader.py                  ← Carregamento de variáveis
```

### **Fluxo de Publicação (Futuro - com Credenciais)**

Quando o usuário quiser **publicar de verdade** em Confluence (não apenas preview local):

```
1. CLI pergunta: "Deseja publicar em Confluence? (s/n)"
   └─ Se não: apenas salva preview local ✅ (MVP atual)
   
2. Se sim:
   └─ Carrega credenciais de config/.env
   └─ Usa ConfluencePublisher.publish() com API REST
   └─ Cria/atualiza página em Confluence
   └─ Retorna URL da página publicada
```

### **Segurança**

- ✅ Arquivo `.env` **NÃO deve ser commitado** (adicionar em `.gitignore`)
- ✅ Token API deve ter **permissões mínimas** (criar/editar páginas apenas)
- ✅ Em CI/CD: usar **secrets** do GitHub/GitLab (não arquivos `.env`)
- ✅ Logs **NUNCA devem conter** tokens ou senhas (usar masking)

---

## Resumo das Mudanças (Simplificação para UX Mínimal)

### **Antes (Versão Anterior - Não Implementada)**
- ❌ CLI pedia múltiplos inputs: URL, plataforma, espaço, título, labels, parent
- ❌ Publicava direto em Confluence via API REST (requerendo credenciais)
- ❌ Usuário responsável por metadados (título, labels, etc.)

### **Agora (Versão Nova - MVP - SIMPLIFICADA)**
- ✅ CLI pede apenas: **URL + Publisher** (2 inputs)
- ✅ Sistema **extrai automaticamente**: Título (`info.title`), Labels (`tags` + `version`), Endpoints
- ✅ Gera **preview em HTML responsivo** em `output/publisher/confluence/index.html`
- ✅ Salva também **Storage Format XML** em `output/publisher/confluence/index.xml`
- ✅ **Nenhuma credencial necessária** no MVP (preview é local)
- ✅ Renderização visual **elegante com CSS inline** (sem JS externo)
- ✅ Abre preview **automaticamente no navegador**

### **Publicação em Confluence (Futuro - Fase 2)**
- 🔜 Quando implementado: carrega credenciais de `config/.env`
- 🔜 Usa ConfluencePublisher para enviar a página via API REST
- 🔜 Retorna URL da página publicada em Confluence
- 🔜 Idempotência: atualiza se página já existe

### **Fluxo Simplificado (MVP - Preview Local)**
```
Usuário: URL + Publisher [confluence]
         ↓
System: Parse → Map → Normalize → AutoInfer(title, labels, endpoints)
         ↓
System: Render HTML (elegante) + XML (Storage Format)
         ↓
Output: output/publisher/confluence/
         ├── index.html (visual preview)
         ├── index.xml (storage format - pronto para publicar depois)
         └── assets/ (imagens, exemplos)
         ↓
CLI: "✅ Sucesso! Preview gerado:"
     "📄 output/publisher/confluence/index.html"
     "🌐 Abrindo no navegador..."
     
FUTURO: Usuário poderá publicar em Confluence com credenciais em config/.env
```

### **Vantagens**
- 🎯 **UX Mínimal**: Apenas 2 perguntas ao usuário
- 🎨 **Visual Elegante**: Templates HTML responsivos com CSS inline
- ⚡ **Rápido**: Não aguarda API Confluence
- 🔄 **Iterativo**: Usuário pode visualizar, iterar, depois publicar
- 🚀 **Extensível**: Futuramente: click-to-publish em Confluence, GitHub Pages, etc.

---

## Estrutura de Publicação no Confluence (Múltiplas Páginas)

Quando o usuário publicar em Confluence (Fase 2), o sistema criará uma **hierarquia de páginas** organizada por:
- **Header** (Página raiz com metadados da API)
- **Endpoints** (Agrupados por tag/tópico)
- **Data Schemas** (Definições de tipos)
- **Authentication** (Configurações de segurança)

### **Exemplo: Petstore API**

```
Petstore API (Página Raiz - Header)
│
├── 📋 Versão: 2.0
├── 🌐 Servidores: https://petstore.swagger.io/v2
├── 📝 Descrição: A sample API that uses petstore
├── 🏷️ Tags: petstore, pets, store
└── 🔐 Segurança: API Key
    │
    ├── 🔌 Endpoints
    │   │
    │   ├── pet (Página Pai - Tópico)
    │   │   ├── Everything about your Pets
    │   │   │
    │   │   ├── PUT /pet (Página Filho)
    │   │   │   └── Update an existing pet
    │   │   │
    │   │   ├── POST /pet (Página Filho)
    │   │   │   └── Add a new pet
    │   │   │
    │   │   ├── GET /pet/findByStatus (Página Filho)
    │   │   │   └── Finds Pets by status
    │   │   │
    │   │   ├── GET /pet/findByTags (Página Filho)
    │   │   │   └── Finds Pets by tags
    │   │   │
    │   │   ├── GET /pet/{petId} (Página Filho)
    │   │   │   └── Find pet by ID
    │   │   │
    │   │   ├── POST /pet/{petId} (Página Filho)
    │   │   │   └── Updates a pet in the store
    │   │   │
    │   │   ├── DELETE /pet/{petId} (Página Filho)
    │   │   │   └── Deletes a pet
    │   │   │
    │   │   ├── POST /pet/{petId}/uploadImage (Página Filho)
    │   │       └── uploads an image
    │   │
    │   └── store (Página Pai - Tópico)
    │       ├── Access to Petstore orders
    │       │
    │       ├── GET /store/inventory (Página Filho)
    │       │   └── Returns pet inventories by status
    │       │
    │       ├── POST /store/order (Página Filho)
    │       │   └── Place an order for a pet
    │       │
    │       ├── GET /store/order/{orderId} (Página Filho)
    │       │   └── Find purchase order by ID
    │       │
    │       └── DELETE /store/order/{orderId} (Página Filho)
    │           └── Delete purchase order by ID
    │
    ├── 📊 Data Schemas
    │   │
    │   ├── Pet (Página)
    │   │   ├── id: integer
    │   │   ├── category: Category
    │   │   ├── name: string (required)
    │   │   ├── photoUrls: array[string]
    │   │   ├── tags: array[Tag]
    │   │   └── status: string (available, pending, sold)
    │   │
    │   ├── Category (Página)
    │   │   ├── id: integer
    │   │   └── name: string
    │   │
    │   ├── Tag (Página)
    │   │   ├── id: integer
    │   │   └── name: string
    │   │
    │   ├── Order (Página)
    │   │   ├── id: integer
    │   │   ├── petId: integer
    │   │   ├── quantity: integer
    │   │   ├── shipDate: datetime
    │   │   ├── status: string (placed, approved, delivered)
    │   │   └── complete: boolean
    │   │
    │   └── ApiResponse (Página)
    │       ├── code: integer
    │       ├── type: string
    │       └── message: string
    │
    └── 🔐 Authentication
        │
        ├── api_key (Página)
        │   ├── Tipo: API Key
        │   ├── Localização: header
        │   ├── Nome do parâmetro: api_key
        │   └── Descrição: API key for petstore
        │
        └── petstore_auth (Página)
            ├── Tipo: OAuth 2.0
            ├── Flow: implicit
            ├── Authorization URL: https://petstore.swagger.io/oauth/authorize
            └── Scopes:
                ├── write:pets - modify pets in your account
                └── read:pets - read your pets
```

### **Estrutura de Pastas no Confluence (Visão Técnica)

Quando publicado via API Confluence, a hierarquia ficaria assim:

```
Petstore API (pageId: 111)
│
├── Endpoints (pageId: 112, parent: 111)
│   │
│   ├── pet (pageId: 113, parent: 112) ← Página Pai (Tópico)
│   │   ├── Everything about your Pets
│   │   │
│   │   ├── PUT /pet (pageId: 114, parent: 113)
│   │   ├── POST /pet (pageId: 115, parent: 113)
│   │   ├── GET /pet/findByStatus (pageId: 116, parent: 113)
│   │   ├── GET /pet/findByTags (pageId: 117, parent: 113)
│   │   ├── GET /pet/{petId} (pageId: 118, parent: 113)
│   │   ├── POST /pet/{petId} (pageId: 119, parent: 113)
│   │   ├── DELETE /pet/{petId} (pageId: 120, parent: 113)
│   │   └── POST /pet/{petId}/uploadImage (pageId: 121, parent: 113)
│   │
│   └── store (pageId: 130, parent: 112) ← Página Pai (Tópico)
│       ├── Access to Petstore orders
│       │
│       ├── GET /store/inventory (pageId: 131, parent: 130)
│       ├── POST /store/order (pageId: 132, parent: 130)
│       ├── GET /store/order/{orderId} (pageId: 133, parent: 130)
│       └── DELETE /store/order/{orderId} (pageId: 134, parent: 130)
│
├── Data Schemas (pageId: 140, parent: 111)
│   └── ... (schemas como páginas)
│
└── Authentication (pageId: 150, parent: 111)
    └── ... (schemes como páginas)
```

---

## 🔗 Exemplos de Links Públicos por Plataforma

Para entender melhor cada plataforma, aqui estão exemplos reais que você pode visitar:

### **Tier 1: MUITO FÁCIL**

#### **MkDocs**
```
Exemplos públicos:
📚 https://www.mkdocs.org/                      (MkDocs próprio)
📚 https://python-poetry.org/                   (Poetry - gerenciador Python)
📚 https://fastapi.tiangolo.com/                (FastAPI - framework web)
📚 https://docs.pytest.org/                     (pytest - testing framework)
📚 https://squidfunk.github.io/mkdocs-material/ (Material for MkDocs - tema)
```

#### **Swagger UI**
```
Exemplos públicos:
🎨 https://petstore.swagger.io/                 (Swagger Petstore oficial!)
🎨 https://editor.swagger.io/                   (Swagger Editor online)
🎨 https://api.github.com/swagger.json          (GitHub API)
```

#### **Jekyll / Hugo**
```
Exemplos públicos:
🚀 https://jekyllrb.com/                        (Jekyll próprio)
🚀 https://gohugo.io/                           (Hugo próprio)
🚀 https://kubernetes.io/                       (Kubernetes - Hugo!)
🚀 https://prometheus.io/                       (Prometheus - Hugo!)
```

---

### **Tier 2: FÁCIL**

#### **Notion**
```
Exemplos públicos:
💡 https://www.notion.so/templates              (Notion templates públicos)
💡 https://publish.obsidian.md/help             (Obsidian Help - usa Notion)
💡 https://github.com/kyrolabs/awesome-notion  (Coleção de workspaces)
```

#### **Obsidian Publish**
```
Exemplos públicos:
🧠 https://publish.obsidian.md/help             (Obsidian Help próprio)
🧠 https://publish.obsidian.md/hub              (Obsidian Hub - community)
🧠 https://notes.nicolevanderhoeven.com/        (Exemplo de usuário)
```

---

### **Tier 3: MÉDIO**

#### **Gitbook**
```
Exemplos públicos (os mais profissionais!):
📕 https://docs.gitbook.com/                    (Gitbook próprio)
📕 https://stripe.com/docs                      (Stripe API - muito usado!)
📕 https://supabase.com/docs                    (Supabase - Firebase alt)
📕 https://docs.anthropic.com/                  (Anthropic Claude API)
📕 https://docs.runwayml.com/                   (Runway ML - API docs)
```

#### **Readme.com**
```
Exemplos públicos (documentação + playground):
📖 https://docs.readme.com/                     (Readme próprio)
📖 https://docs.twilio.com/                     (Twilio - comunicações)
📖 https://developers.stripe.com/docs           (Stripe - usa Readme)
```

#### **Redoc (Swagger Moderno)**
```
Exemplos públicos (mais bonito que Swagger UI):
🎨 https://redoc.ly/                            (Redoc próprio)
🎨 https://redocly.com/openapi/petstore/        (Petstore em Redoc)
🎨 https://developer.stripe.com/openapi         (Stripe OpenAPI)
```

#### **Docusaurus**
```
Exemplos públicos (moderno + React):
⚛️ https://docusaurus.io/                       (Docusaurus próprio)
⚛️ https://facebook.github.io/react-native/     (React Native)
⚛️ https://reactjs.org/docs                      (React oficial)
⚛️ https://angular.io/docs                       (Angular)
⚛️ https://pytorch.org/docs/stable/index.html    (PyTorch)
```

---

### **Tier 4: COMPLEXO**

#### **Confluence Cloud**
```
Exemplos públicos:
💼 https://support.atlassian.com/confluence-cloud/
💼 https://docs.atlassian.com/
⚠️  Maioria é privada (intranet corporate)
```

#### **SharePoint Online**
```
Exemplos públicos:
🏢 https://support.microsoft.com/en-us/office
🏢 https://docs.microsoft.com/en-us/
⚠️  Maioria é privada (enterprise)
```

#### **Jira ServiceDesk**
```
Exemplos públicos:
🎫 https://support.atlassian.com/
⚠️  Maioria é privada (internal support)
```

---

### **Tier 5: MUITO COMPLEXO**

#### **Slack**
```
Exemplos públicos:
💬 https://api.slack.com/docs                   (Slack API docs)
⚠️  Mensagens são efêmeras (não URL permanente)
```

#### **Azure DevOps Wiki**
```
Exemplos públicos:
🔵 https://docs.microsoft.com/en-us/azure/
⚠️  Maioria é privada (enterprise)
```

#### **Storybook Docs**
```
Exemplos públicos:
📚 https://storybook.js.org/                    (Storybook próprio)
📚 https://www.chromatic.com/                   (Chromatic - build)
```

---

## 📊 Resumo: TOP 5 MAIS USADOS PUBLICAMENTE

1. **Swagger UI** - https://petstore.swagger.io/
2. **MkDocs** - https://fastapi.tiangolo.com/
3. **Gitbook** - https://stripe.com/docs
4. **GitHub Pages** - Qualquer repo com `/docs`
5. **Docusaurus** - https://reactjs.org/docs

---

## 🎯 Recomendação: PRÓXIMOS PASSOS

Depois do MVP (Confluence Preview Local), a ordem sugerida é:

1. **GitHub Pages** (2-3h) - Quick win, muito fácil
2. **MkDocs** (2-3h) - Popular entre Python devs
3. **Swagger UI** (1-2h) - Comunidade OpenAPI adora
4. **Notion** (2-3h) - Trending, SaaS moderno
5. **Confluence Cloud** (5-7h) - Enterprise (já planejado)

Cada um pode ser implementado independentemente sem quebrar os outros!

---
