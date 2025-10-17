from src.presentation.agent_controller import AIAgent


def main() -> None:
    # Primeiro exemplo de uso do AIAgent
    provider = "openai"  # ou "ollama"
    model = "gpt-5-mini"  # ou outro modelo suportado
    name = "AgenteTeste"
    instructions = "Responda como um assistente educado."

    agent = AIAgent(
        provider=provider, model=model, name=name, instructions=instructions
    )
    print(f"Agente criado: {agent}")

    # Segundo exemplo de uso do AIAgent
    agent2 = AIAgent(
        provider="ollama",
        model="phi4-mini:latest",
        name="Agente Tests",
        instructions="Responda como uma pessoa extremamente culta",
    )

    # Exemplo de chat
    user_message = "Olá, quem é você?"
    response = agent2.chat(user_message)
    print(f"Resposta do agente: {response}")

    # Terceiro exemplo: Agente sem name e instructions (opcionais)
    agent3 = AIAgent(
        provider="openai",
        model="gpt-5-mini",
    )
    print("\nAgente 3 criado apenas com provider e model")
    configs = agent3.get_configs()
    print(f"Name: {configs['name']}, Instructions: {configs['instructions']}")


if __name__ == "__main__":
    main()
