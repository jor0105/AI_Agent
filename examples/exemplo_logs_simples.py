#!/usr/bin/env python3
"""
EXEMPLO SUPER SIMPLES - Como os Logs Funcionam

Execute: python3 exemplo_logs_simples.py
"""

import logging

from src.infra.config.logging_config import LoggingConfig
from src.presentation.agent_controller import AIAgent


def exemplo_basico():
    """Exemplo mais básico possível."""
    print("=" * 60)
    print("EXEMPLO 1: Logs no Terminal (Automático)")
    print("=" * 60)

    # Configure APENAS UMA VEZ (no início)
    LoggingConfig.configure(level=logging.INFO)

    print("\n👉 Criando um agente...")
    agent = AIAgent(
        provider="ollama",
        model="phi4-mini:latest",
        name="Assistente Simples",
        instructions="Você é um assistente prestativo.",
    )

    print("\n👉 Conversando com o agente...")
    response = agent.chat("Olá! Tudo bem?")

    print("\n✅ Resposta do agente:")
    print(f"   {response[:100]}...")

    print("\n" + "=" * 60)
    print("VEJA ACIMA ⬆️ - Os logs apareceram automaticamente!")
    print("=" * 60)


def exemplo_com_arquivo():
    """Exemplo salvando logs em arquivo."""
    print("\n\n" + "=" * 60)
    print("EXEMPLO 2: Logs em Arquivo (Salvos)")
    print("=" * 60)

    # Configure para salvar em arquivo
    LoggingConfig.reset()  # Limpa configuração anterior
    LoggingConfig.configure(
        level=logging.INFO, log_to_file=True, log_file_path="logs/exemplo_simples.log"
    )

    print("\n👉 Criando um agente...")
    agent = AIAgent(
        provider="ollama",
        model="phi4-mini:latest",
        name="Assistente com Logs",
        instructions="Você é um assistente prestativo.",
    )

    print("\n👉 Conversando com o agente...")
    response = agent.chat("Me conte uma piada curta.")

    print("\n✅ Resposta do agente:")
    print(f"   {response[:100]}...")

    print("\n📁 Logs foram salvos em: logs/exemplo_simples.log")
    print("   Execute: cat logs/exemplo_simples.log")

    print("\n" + "=" * 60)
    print("AGORA os logs também estão salvos em arquivo!")
    print("=" * 60)


def exemplo_com_erro():
    """Exemplo mostrando como erros aparecem."""
    print("\n\n" + "=" * 60)
    print("EXEMPLO 3: Logs de Erro (Automático)")
    print("=" * 60)

    LoggingConfig.reset()
    LoggingConfig.configure(level=logging.INFO)

    print("\n👉 Criando um agente...")
    agent = AIAgent(
        provider="ollama",
        model="phi4-mini:latest",
        name="Assistente de Teste",
        instructions="Você é um assistente.",
    )

    print("\n👉 Tentando enviar mensagem VAZIA (vai dar erro)...")
    try:
        _ = agent.chat("")  # ❌ Mensagem vazia causa erro
    except Exception as e:
        print(f"\n❌ ERRO CAPTURADO: {str(e)}")

    print("\n" + "=" * 60)
    print("VEJA ACIMA ⬆️ - O log de erro apareceu automaticamente!")
    print("Com detalhes técnicos (stacktrace) para debug")
    print("=" * 60)


def exemplo_debug():
    """Exemplo com mais detalhes (modo DEBUG)."""
    print("\n\n" + "=" * 60)
    print("EXEMPLO 4: Modo DEBUG (Muitos Detalhes)")
    print("=" * 60)

    LoggingConfig.reset()
    LoggingConfig.configure(level=logging.DEBUG)  # ← DEBUG = muito detalhe

    print("\n👉 Criando um agente...")
    agent = AIAgent(
        provider="ollama",
        model="phi4-mini:latest",
        name="Assistente Debug",
        instructions="Seja breve.",
    )

    print("\n👉 Conversando com o agente...")
    response = agent.chat("Diga 'olá'")

    print("\n✅ Resposta:")
    print(f"   {response}")

    print("\n" + "=" * 60)
    print("MODO DEBUG mostra MUITO mais informação!")
    print("Útil para encontrar problemas")
    print("=" * 60)


def demonstracao_completa():
    """Demonstração completa do sistema de logs."""
    print("\n" + "🎓" * 30)
    print("DEMONSTRAÇÃO COMPLETA - Sistema de Logs Automático")
    print("🎓" * 30 + "\n")

    print("📋 O QUE VOCÊ VAI VER:")
    print("   1. Logs no terminal (automático)")
    print("   2. Logs salvos em arquivo")
    print("   3. Logs de erro (automático)")
    print("   4. Modo debug (detalhado)")
    print("\n👉 IMPORTANTE: Você NÃO precisa adicionar código de log!")
    print("   Tudo já está funcionando automaticamente!\n")

    input("Pressione ENTER para começar...")

    # Executa exemplos
    exemplo_basico()
    input("\nPressione ENTER para próximo exemplo...")

    exemplo_com_arquivo()
    input("\nPressione ENTER para próximo exemplo...")

    exemplo_com_erro()
    input("\nPressione ENTER para próximo exemplo...")

    exemplo_debug()

    print("\n\n" + "🎉" * 30)
    print("DEMONSTRAÇÃO COMPLETA!")
    print("🎉" * 30)

    print("\n✅ O QUE VOCÊ APRENDEU:")
    print("   ✓ Logs aparecem automaticamente no terminal")
    print("   ✓ Podem ser salvos em arquivo")
    print("   ✓ Erros são logados automaticamente")
    print("   ✓ Você controla o nível de detalhe")
    print("   ✓ Dados sensíveis são protegidos automaticamente")

    print("\n📚 PRÓXIMOS PASSOS:")
    print("   1. Leia: docs/LOGGING_GUIA_INICIANTES.md")
    print("   2. Configure no seu main.py")
    print("   3. Use seu sistema normalmente")
    print("   4. Os logs cuidam do resto!")

    print("\n🚀 É ISSO! Simples assim!\n")


if __name__ == "__main__":
    try:
        demonstracao_completa()
    except KeyboardInterrupt:
        print("\n\n👋 Demonstração cancelada. Até mais!")
    except Exception as e:
        print(f"\n❌ Erro durante demonstração: {e}")
        print("Verifique se o sistema está configurado corretamente.")
