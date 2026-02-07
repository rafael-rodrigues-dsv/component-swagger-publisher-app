"""
Interactive test for real Confluence publication
Run this to test full publication to Confluence
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.services.PublishingService import PublishingService
from src.infrastructure.config.config import config
from colorama import init, Fore, Style

init(autoreset=True)

def print_header(text):
    print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")


def test_full_publication():
    """Test complete publication to Confluence"""

    print_header("CONFLUENCE REAL PUBLICATION TEST")

    # Step 1: Check configuration
    print(f"{Fore.CYAN}📋 Step 1: Configuration Check{Style.RESET_ALL}")

    if not config.is_confluence_configured():
        print_error("Confluence NOT configured!")
        print()
        print_info("Please update config/.env with:")
        print("   - CONFLUENCE_BASE_URL")
        print("   - CONFLUENCE_USERNAME (must be EMAIL)")
        print("   - CONFLUENCE_TOKEN")
        print("   - CONFLUENCE_SPACE_KEY")
        print()
        print_warning("Current values:")
        print(f"   Base URL: {config.confluence_base_url or 'NOT SET'}")
        print(f"   Username: {config.confluence_username or 'NOT SET'}")
        print(f"   Token: {'SET' if config.confluence_token else 'NOT SET'}")
        print(f"   Space: {config.confluence_space_key or 'NOT SET'}")
        return 1

    print_success("Configuration loaded!")
    print(f"   Base URL: {config.confluence_base_url}")
    print(f"   Space: {config.confluence_space_key}")
    print(f"   Username: {config.confluence_username}")

    # Check if username is email
    if '@' not in config.confluence_username:
        print()
        print_warning("Username should be an EMAIL for Confluence Cloud!")
        print(f"   Current: {config.confluence_username}")
        print(f"   Expected: your-email@domain.com")
        print()
        print_info("Update CONFLUENCE_USERNAME in config/.env to your Atlassian email")

        proceed = input(f"\n{Fore.YELLOW}Continue anyway? (yes/no) [no]: {Style.RESET_ALL}").strip().lower()
        if proceed != 'yes':
            print_info("Cancelled. Please update config/.env with correct email.")
            return 0

    print()

    # Step 2: Choose API
    print(f"{Fore.CYAN}📋 Step 2: API Selection{Style.RESET_ALL}")
    print()
    print("Which API do you want to publish?")
    print("  1. Petstore API (Swagger 2.0) - Default")
    print("  2. Petstore API (OpenAPI 3.0)")
    print("  3. Custom URL")
    print()

    choice = input(f"{Fore.YELLOW}Choice [1]: {Style.RESET_ALL}").strip()

    if choice == '2':
        spec_url = "https://petstore3.swagger.io/api/v3/openapi.json"
        print_info(f"Selected: OpenAPI 3.0 Petstore")
    elif choice == '3':
        spec_url = input(f"{Fore.YELLOW}Enter OpenAPI spec URL: {Style.RESET_ALL}").strip()
        if not spec_url:
            print_error("URL required!")
            return 1
    else:
        spec_url = "https://petstore.swagger.io/v2/swagger.json"
        print_info(f"Selected: Swagger 2.0 Petstore (default)")

    print()

    # Step 3: Confirm publication
    print_header("⚠️  IMPORTANT - READ CAREFULLY")
    print_warning("This will CREATE or UPDATE a real page in Confluence!")
    print()
    print("📄 What will happen:")
    print("   1. Parse the OpenAPI specification")
    print("   2. Generate documentation content")
    print("   3. Connect to Confluence API")
    print("   4. Create/Update page in your Confluence space")
    print("   5. Return the URL of the published page")
    print()
    print(f"📍 Target:")
    print(f"   Space: {config.confluence_space_key}")
    print(f"   API: {spec_url}")
    print()

    confirm = input(f"{Fore.YELLOW}Proceed with publication? Type 'YES' to confirm: {Style.RESET_ALL}").strip()

    if confirm != 'YES':
        print_info("Publication cancelled by user.")
        return 0

    print()
    print_header("🚀 Publishing to Confluence...")

    try:
        service = PublishingService()

        # Get API info first
        print_info("Analyzing OpenAPI specification...")
        api_info = service.get_api_info(spec_url)

        if 'error' in api_info:
            print_error(f"Failed to analyze specification: {api_info['error']}")
            return 1

        print()
        print_success("API analyzed successfully!")
        print(f"   Title: {api_info['title']}")
        print(f"   Version: {api_info['version']}")
        print(f"   Endpoints: {api_info['endpoint_count']}")
        print()

        # Publish in REAL mode
        print_info("Publishing to Confluence (this may take a few seconds)...")
        result = service.publish_documentation(
            source_url=spec_url,
            publisher_type="confluence",
            mode="publish"  # REAL publication mode
        )

        print()
        print_header("📊 PUBLICATION RESULT")

        if result.success:
            print_success("PUBLICATION SUCCESSFUL!")
            print()

            if result.output_paths:
                print(f"{Fore.GREEN}📄 Pages Created:{Style.RESET_ALL}")
                for page_type, url in result.output_paths.items():
                    print(f"   {page_type}: {url}")
                print()

            if result.url:
                print(f"{Fore.GREEN}🌐 Main Page URL:{Style.RESET_ALL}")
                print(f"   {result.url}")
                print()
                print_info("You can now view the page in Confluence!")

            print(f"⏱️  Duration: {result.duration_seconds:.2f}s")

            if result.warnings:
                print()
                print_warning("Warnings:")
                for warning in result.warnings:
                    print(f"   ⚠️  {warning}")

            return 0

        else:
            print_error("PUBLICATION FAILED!")
            print()
            if result.errors:
                print(f"{Fore.RED}Errors:{Style.RESET_ALL}")
                for error in result.errors:
                    print(f"   ❌ {error}")

            # Provide helpful hints
            print()
            print_info("Common issues:")
            print("   1. Username must be EMAIL (not username)")
            print("   2. API token must have write permissions")
            print("   3. Space must exist and be accessible")
            print("   4. Check network connection to Confluence")

            return 1

    except Exception as e:
        print()
        print_header("❌ EXCEPTION OCCURRED")
        print_error(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    try:
        exit_code = test_full_publication()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print_info("Cancelled by user (Ctrl+C)")
        sys.exit(0)

