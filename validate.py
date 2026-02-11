#!/usr/bin/env python
"""Quick validation test"""
import sys

try:
    print("Testing imports...")
    from src.application.services.publishing_service import PublishingService
    print("✓ PublishingService OK")

    service = PublishingService()
    print("✓ Service instantiated OK")

    print("\n✅ SISTEMA FUNCIONAL!")
    print("\nExecute: python main.py")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

