from .interface.agent_controller import AIAgentController

if __name__ == "__main__":
    agent = AIAgentController(
        model="gpt-5-mini", name="Jordan", prompt="voce é um amigo meu"
    )

    response = agent.chat("me diga que dia é hoje")
    print(f"Resposta: {response}")

    print("\nConfiguração do Agente:")
    print(agent.get_configs())
