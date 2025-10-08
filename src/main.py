from src.interface.agent_controller import AIAgent


def main() -> None:
    agent = AIAgent(
        model="gpt-5-mini", name="Jordan", instructions="voce é um amigo meu"
    )

    response = agent.chat("me diga que dia é hoje")
    print(f"Resposta: {response}")

    print("\nConfiguração do Agente:")
    print(agent.get_configs())


if __name__ == "__main__":
    main()
