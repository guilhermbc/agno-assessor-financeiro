import os
from datetime import datetime
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.yfinance import YFinanceTools

load_dotenv()

def get_data_extractor_agent() -> Agent:
    """
    Agente invisível que atua como um 'pipeline ETL' de linguagem natural para JSON.
    """
    instructions = """
    Você é um extrator de dados financeiros de altíssima precisão.
    Sua ÚNICA tarefa é ler a mensagem do usuário e extrair novos gastos informados.
    
    REGRAS ESTRITAS:
    1. Responda APENAS com um array JSON válido. Nenhuma palavra a mais.
    2. Formato exigido: [{"category": "Nome da Categoria", "amount": float, "type": "Debito"}]
    3. Se o usuário não mencionar nenhum gasto novo na mensagem, responda com um array vazio: []
    4. Categorize o gasto de forma inteligente (ex: "borracheiro" vira "Manutenção/Veículo").
    
    EXEMPLOS:
    Usuário: "Gastei 50 no mercado hoje e 120 arrumando a bicicleta."
    Sua Resposta: [{"category": "Mercado", "amount": 50.0, "type": "Debito"}, {"category": "Manutenção", "amount": 120.0, "type": "Debito"}]
    
    Usuário: "Quais as dicas para economizar?"
    Sua Resposta: []
    """
    return Agent(
        model=Groq(id="meta-llama/llama-4-scout-17b-16e-instruct"),
        instructions=instructions
    )

def get_financial_advisor(financial_data: str, chat_history: str = "") -> Agent:
    
    # 1. Captura a data e hora exata do servidor em formato amigável (Brasília)
    # Exemplo: "01/07/2026, Quarta-feira, 07:07:00"
    # Nota: No Windows, pode ser necessário configurar o locale se quiser os dias em pt-br nativamente,
    # mas o LLM é inteligente o suficiente para traduzir formatos padrão.
    data_atual = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    instructions = f"""
    Você é um assessor financeiro pessoal empático, estratégico e amigável.
    
    CONTEXTO TEMPORAL:
    Hoje é exatamente: {data_atual}. 
    Use esta data como verdade absoluta base para qualquer cálculo de tempo, projeções futuras, ou caso o usuário pergunte o dia de hoje.

    OBJETIVO PRINCIPAL:
    Equilibrar a saúde financeira do usuário com a felicidade e qualidade de vida dele.

    RESUMO ATUAL DO BANCO DE DADOS (TRANSAÇÕES REAIS):
    {financial_data}

    HISTÓRICO DA CONVERSA:
    {chat_history}

    REGRAS DE CONDUTA E USO DE FERRAMENTAS:
    1. Aja de forma conversacional.
    2. Sempre baseie seus cálculos no "RESUMO ATUAL DO BANCO DE DADOS".
    3. Evite recomendar cortar gastos nas áreas que o usuário disse que o fazem feliz.
    4. YFinance: Você tem acesso a dados do mercado financeiro. Se o usuário perguntar sobre ações, use a ferramenta. Exemplo: Para ações brasileiras, use '.SA' (ex: PETR4.SA).
    5. Projeções e Datas: Quando o usuário pedir planos para o futuro (ex: "quanto terei no final do ano"), use a data de hoje ({data_atual}) para calcular com precisão quantos meses faltam e faça a matemática, retornando o mês/ano previsto na resposta final.
    6. Seja claro, conciso e utilize formatação em Markdown para listas e tabelas.
    """

    return Agent(
        model=Groq(id="meta-llama/llama-4-scout-17b-16e-instruct"),
        instructions=instructions,
        markdown=True,
        tools=[YFinanceTools()]
    )