from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq

# Carrega as variáveis contidas no arquivo .env para a memória do script
load_dotenv()

# O Agno agora vai encontrar a chave GROQ_API_KEY que foi carregada ali em cima
agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    markdown=True
)

agent.print_response("Diga 'Hello World' em português e adicione uma frase curta de boas-vindas.")