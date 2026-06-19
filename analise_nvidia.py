import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.yfinance import YFinanceTools
from agno.tools.duckduckgo import DuckDuckGoTools

load_dotenv()

# 1. Configurando as ferramentas que o assessor vai usar
ferramentas_financeiras = YFinanceTools(
    # stock_price=True,        # Preço atual da ação
    # analyst_recommendations=True, # Recomendações de analistas (Buy/Sell)
    # stock_fundamentals=True, # Dados fundamentalistas (P/L, LPA, etc.)
    # company_news=True        # Notícias específicas da empresa
)

# 2. Inicializando o Agente Assessor Financeiro
assessor_financeiro = Agent(
    name="Assessor Financeiro Inteligente",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[ferramentas_financeiras, DuckDuckGoTools()], # Combina dados do Yahoo e buscas na web
    instructions=[
        "Você é um assessor financeiro sênior e analista de investimentos experiente.",
        "Seu tom deve ser profissional, analítico, seguro e direto ao ponto.",
        "Sempre use tabelas de Markdown para apresentar dados numéricos, históricos ou comparações de ações.",
        "Sempre verifique as notícias mais recentes e os fundamentos da empresa antes de dar uma opinião.",
        "Importante: Adicione um aviso legal (Disclaimer) no final de análises mais profundas informando que suas respostas são apenas informativas e não configuram recomendação direta de compra/venda.",
    ],
    # show_tool_calls=True,  # Mostra no terminal quais ferramentas o agente está acionando
    markdown=True,         # Formata a saída perfeitamente
)

# 3. Testando o assessor com uma análise complexa
assessor_financeiro.print_response(
    "Faça uma análise rápida da Nvidia (NVDA). Quero saber o preço atual, o que os analistas "
    "estão recomendando e as últimas notícias que podem impactar a empresa.",
    stream=True # Retorna a resposta em tempo real conforme ela é gerada
)