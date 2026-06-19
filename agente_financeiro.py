import os
import pandas as pd
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool

# Carrega as variáveis de ambiente (sua chave do Groq)
load_dotenv()

# 1. Criando a Ferramenta (Tool) para ler os dados sintéticos


@tool
def ler_extrato_bancario() -> str:
    """Lê o extrato bancário sintético do usuário e retorna os dados para análise."""
    caminho = "dados/extrato_sintetico.csv"
    if not os.path.exists(caminho):
        return "Erro: Arquivo não encontrado. Rode o script gerar_dados.py primeiro."

    # Lê o CSV e converte para uma string que o LLM consegue entender
    df = pd.read_csv(caminho)
    return df.to_string(index=False)


# 2. Configurando o Agente Mínimo
agente = Agent(
    name="Assessor Financeiro Pessoal",
    # Pode trocar por Ollama se for usar o Dockerfile
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[ler_extrato_bancario],
    instructions=[
        "Você é um assessor financeiro pessoal.",
        "Sempre use a ferramenta 'ler_extrato_bancario' para consultar os gastos antes de responder.",
        "Categorize as despesas automaticamente e identifique padrões, como assinaturas recorrentes ou gastos ambíguos.",
        "Seja direto, analítico e responda em português.",
    ],
    debug_mode=True,  # Fundamental para a 'Análise dos reasoning traces' exigida no trabalho
    markdown=True
)

# 3. Teste da Semana 1
if __name__ == "__main__":
    print("\n--- Iniciando Assessor Financeiro (Semana 1) ---\n")

    pergunta_usuario = (
        "Analise meu extrato deste mês. Quais foram os meus maiores gastos? "
        "Existe alguma assinatura que eu estou pagando e poderia cancelar?"
    )

    agente.print_response(pergunta_usuario, stream=True)
