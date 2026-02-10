"""
CLI Main Entry Point - Minimal UX
"""
import sys
import os
import webbrowser
from pathlib import Path
from colorama import init, Fore, Style

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.application.services.publishing_service import PublishingService

# Initialize colorama
init(autoreset=True)


def print_banner():
    """Print application banner"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}  OpenAPI Documentation Publisher")
    print(f"{Fore.CYAN}  Version 1.0.0 - MVP Phase 1")
    print(f"{Fore.CYAN}{'=' * 60}\n")


def print_success(message):
    """Print success message"""
    print(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")


def print_error(message):
    """Print error message"""
    print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")


def print_info(message):
    """Print info message"""
    print(f"{Fore.BLUE}[INFO] {message}{Style.RESET_ALL}")


def print_warning(message):
    """Print warning message"""
    print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")


def get_user_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    value = input(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}").strip()
    return value if value else default


def main():
    """Main CLI function"""
    print_banner()

    # Get OpenAPI specification URL
    print(f"{Fore.CYAN}>>> Step 1: OpenAPI Specification{Style.RESET_ALL}")
    spec_url = get_user_input(
        "Enter URL or path to OpenAPI specification",
        default="https://petstore.swagger.io/v2/swagger.json"
    )

    if not spec_url:
        print_error("Specification URL is required!")
        return 1

    print()

    # Get publisher type
    print(f"{Fore.CYAN}>>> Step 2: Publisher Selection{Style.RESET_ALL}")
    print()
    print("Available publishers:")
    print("  1. Confluence")
    print()
    publisher_choice = get_user_input("Select publisher", default="1")

    # Map choice to publisher
    publisher_map = {
        "1": "confluence",
        "confluence": "confluence"
    }
    publisher = publisher_map.get(publisher_choice.lower(), "confluence")

    print()

    # Get publication mode for Confluence
    publish_mode = "preview"  # Default to preview
    if publisher.lower() == "confluence":
        print(f"{Fore.CYAN}>>> Step 3: Publication Mode{Style.RESET_ALL}")
        print()
        print("Available modes:")
        print("  1. Preview - Generate Confluence-like HTML locally")
        print("  2. Publish - Send to real Confluence server (requires config)")
        print()
        mode_choice = get_user_input("Select mode (1-2)", default="1")

        # Map choice to mode
        mode_map = {
            "1": "preview",
            "2": "publish",
            "preview": "preview",
            "publish": "publish"
        }
        publish_mode = mode_map.get(mode_choice.lower(), "preview")
        print()

    print()
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print_info(f"Processing: {spec_url}")
    print_info(f"Publisher: {publisher}")
    if publisher.lower() == "confluence":
        print_info(f"Mode: {publish_mode.upper()}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

    # Process
    try:
        service = PublishingService()

        # Show API info
        print_info("Analyzing OpenAPI specification...")
        api_info = service.get_api_info(spec_url)

        if 'error' in api_info:
            print_error(f"Failed to analyze specification: {api_info['error']}")
            return 1

        print()
        print(f"{Fore.GREEN}[API Information]{Style.RESET_ALL}")
        print(f"   Title: {api_info['title']}")
        print(f"   Version: {api_info['version']}")
        print(f"   OpenAPI: {api_info['openapi_version']}")
        print(f"   Endpoints: {api_info['endpoint_count']}")
        if api_info['tags']:
            print(f"   Tags: {', '.join(api_info['tags'])}")
        print()

        # Publish
        print_info("Generating documentation...")
        result = service.publish_documentation(spec_url, publisher, mode=publish_mode)

        if not result.success:
            print_error("Publishing failed!")
            for error in result.errors:
                print(f"   {Fore.RED}{error}{Style.RESET_ALL}")
            return 1

        # Success!
        print()
        print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
        if publisher.lower() == "confluence" and publish_mode == "preview":
            print_success("Confluence Preview generated successfully!")
            print(f"{Fore.CYAN}   This preview simulates multi-page Confluence structure{Style.RESET_ALL}")
        else:
            print_success("Documentation generated successfully!")
        print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}[Output Files]{Style.RESET_ALL}")
        for file_type, file_path in result.output_paths.items():
            print(f"   {file_type.upper()}: {file_path}")

        print()
        print(f"{Fore.CYAN}[Processing time: {result.duration_seconds:.2f}s]{Style.RESET_ALL}")

        if result.warnings:
            print()
            for warning in result.warnings:
                print_warning(warning)

        # Open in browser
        if 'html' in result.output_paths:
            print()
            open_browser = get_user_input("Open preview in browser? (y/n)", default="y")
            if open_browser.lower() in ['y', 'yes', '']:
                html_path = result.output_paths['html']
                print_info(f"Opening {html_path}...")
                webbrowser.open(f'file://{html_path}')

        print()
        print_success("Done!")
        return 0

    except KeyboardInterrupt:
        print()
        print_warning("Operation cancelled by user")
        return 130
    except Exception as e:
        print()
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

