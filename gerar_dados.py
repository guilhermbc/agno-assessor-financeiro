import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
import os


# Inicializa o Faker (em português)
fake = Faker('pt_BR')

def gerar_extrato(num_transacoes=50):
    dados = []
    data_atual = datetime.now()
    
    # Lista de possíveis descrições para forçar o Agno a pensar na categorização
    descricoes_claras = [
        "Supermercado Extra", "Posto Ipiranga", "Uber", "Ifood", 
        "Farmácia Pague Menos", "Conta de Luz - EDP", "Conta de Água - Cesan"
    ]
    
    # Assinaturas que o Agno deve identificar como recorrentes [cite: 158]
    assinaturas = ["Netflix", "Spotify", "Amazon Prime", "Academia SmartFit"]
    
    # Gastos ambíguos para testar a avaliação crítica exigida no trabalho [cite: 162]
    ambiguos = ["Pix para Joao Silva", "Pagamento Loja 123", "Transferência DOC", "Compra MercadoPago"]

    # Adiciona a renda mensal
    dados.append({
        "Data": (data_atual - timedelta(days=30)).strftime("%d/%m/%Y"),
        "Descricao": "Salario Mensal",
        "Valor": 6500.00,
        "Tipo": "Credito"
    })

    # Gera transações aleatórias
    for i in range(num_transacoes):
        dias_atras = random.randint(1, 30)
        data_transacao = (data_atual - timedelta(days=dias_atras)).strftime("%d/%m/%Y")
        
        # Escolhe aleatoriamente o tipo de gasto
        categoria_sorteio = random.choice(['claro', 'assinatura', 'ambiguo'])
        
        if categoria_sorteio == 'claro':
            descricao = random.choice(descricoes_claras)
            valor = round(random.uniform(20.0, 450.0), 2)
        elif categoria_sorteio == 'assinatura':
            descricao = random.choice(assinaturas)
            valor = round(random.uniform(19.90, 120.0), 2)
        else:
            descricao = random.choice(ambiguos)
            valor = round(random.uniform(50.0, 800.0), 2)
            
        dados.append({
            "Data": data_transacao,
            "Descricao": descricao,
            "Valor": -valor,  # Negativo para representar saída
            "Tipo": "Debito"
        })

    # Cria o DataFrame e salva em CSV
    df = pd.DataFrame(dados)
    
    # Ordena por data
    df['Data'] = pd.to_datetime(df['Data'], format="%d/%m/%Y")
    df = df.sort_values(by="Data").reset_index(drop=True)
    df['Data'] = df['Data'].dt.strftime("%d/%m/%Y")
    
    # Cria a pasta 'dados' se não existir
    os.makedirs('dados', exist_ok=True)
    caminho_arquivo = 'dados/extrato_sintetico.csv'
    
    df.to_csv(caminho_arquivo, index=False)
    print(f"✅ Extrato sintético gerado com sucesso em: {caminho_arquivo}")
    print(df.head(10))

if __name__ == "__main__":
    print("Gerando dados financeiros sintéticos (Faker)...")
    gerar_extrato()