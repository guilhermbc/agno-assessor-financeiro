import reflex as rx
import pandas as pd
import io
import json
import re
from .agent import get_financial_advisor, get_data_extractor_agent

# --- MODELOS DE BANCO DE DADOS (ORM) ---
class ChatMessage(rx.Model, table=True):
    role: str
    content: str
    session_id: str = "default_user"

class Transaction(rx.Model, table=True):
    category: str
    amount: float
    type: str 
    session_id: str = "default_user"

# --- ESTADO DA APLICAÇÃO ---
class AdvisorState(rx.State):
    # Removida a variável 'current_message' para otimização de performance. Agora usamos formulário.
    chat_history: list[dict[str, str]] = []
    chart_data: list[dict[str, any]] = []
    database_summary: str = ""
    
    is_loading: bool = False
    is_uploading: bool = False

    def on_load(self):
        """Carrega e calcula os dados do banco para o Dashboard e para o Agente."""
        with rx.session() as db:
            messages = db.query(ChatMessage).filter(ChatMessage.session_id == "default_user").all()
            if not messages:
                welcome_msg = ChatMessage(role="agent", content="Olá! 👋 Sou seu Assessor Financeiro Pessoal. O que te faz feliz no tempo livre?")
                db.add(welcome_msg)
                db.commit()
                messages = [welcome_msg]
            
            self.chat_history = [{"role": m.role, "content": m.content} for m in messages]
            
            transactions = db.query(Transaction).filter(Transaction.session_id == "default_user").all()
            
            category_totals = {}
            total_gastos = 0
            for t in transactions:
                if t.type.lower() == "debito":
                    category_totals[t.category] = category_totals.get(t.category, 0) + abs(t.amount)
                    total_gastos += abs(t.amount)

            ## Mostrando cores diferentes no grafico de pizza 
            paleta_financeira = [
                "#3b82f6",  # Azul Royal
                "#10b981",  # Verde Esmeralda (Principal)
                "#ef4444",  # Vermelho Alerta (para débitos altos, se quiser)
                "#f97316",  # Laranja Vívido
                "#14b8a6",  # Teal
                "#8b5cf6",  # Roxo Violeta
                "#f59e0b",  # Âmbar
                "#06b6d4",  # Ciano
                "#a855f7",  # Púrpura
            ]
            self.chart_data = [
                {
                    "name": str(k), # Garante que a chave seja string para o eixo
                    "value": float(v), # Garante que o valor seja float/int
                    # Escolhe a cor baseada no índice i na lista paleta_financeira
                    "fill": paleta_financeira[i % len(paleta_financeira)]
                }
                # category_totals é o resultado do groupby do pandas transformado em dict
                for i, (k, v) in enumerate(category_totals.items())
            ]
            
            self.database_summary = f"Total Gasto Registrado: R$ {total_gastos:.2f}\nDetalhamento:\n"
            for k, v in category_totals.items():
                self.database_summary += f"- {k}: R$ {v:.2f}\n"

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Lê o CSV real enviado pelo usuário e salva no Banco de Dados."""
        self.is_uploading = True
        yield

        with rx.session() as db:
            db.add(ChatMessage(role="agent", content="Lendo seu arquivo de transações..."))
            db.commit()
        self.on_load() # Atualiza UI
        try:
            file = files[0]
            upload_data = await file.read()
            df = pd.read_csv(
                io.BytesIO(upload_data),
                header=None,
                names=["data", "descricao", "valor", "tipo"],
                encoding="utf-8" # Garante a leitura correta de acentos como 'Crédito'
            )
            print(df.head())
            df.columns = df.columns.str.strip()
            
            with rx.session() as db:
                for linha in df.itertuples(index=False):
                    # Remove espaços em branco das strings
                    descricao_limpa = linha.descricao.strip()
                    tipo_limpo = linha.tipo.strip()

                    print(f"Transação: {linha.data} - {descricao_limpa} | R$ {linha.valor} ({tipo_limpo})")
                    
                    # Colocar data no banco ...
                    db.add(Transaction(category=descricao_limpa, amount=linha.valor, type=tipo_limpo))

                db.commit()
                print("Transações cadastradas no banco.")  

                db.add(ChatMessage(role="agent", content="✅ **CSV processado e salvo no banco de dados!** O gráfico já foi atualizado."))
                db.commit()
            self.on_load() # Atualiza UI

            
        except Exception as e:
            print("Erro no upload. ", e)

            with rx.session() as db:
                db.add(ChatMessage(role="agent", content="❌ Ocorreu um erro ao tentar salvar os dados da sua planilha... Tente novamente."))
                db.commit()
            self.on_load() # Atualiza UI
            
        self.is_uploading = False
        yield

    def extract_transactions_from_text(self, text: str):
        """Passo 1 da Orquestração: Roda o Agente Extrator para pescar gastos do chat."""
        extractor = get_data_extractor_agent()
        response = extractor.run(text)
        
        match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if match:
            try:
                novos_gastos = json.loads(match.group(0))
                if novos_gastos:
                    with rx.session() as db:
                        for gasto in novos_gastos:
                            db.add(Transaction(
                                category=gasto.get("category", "Geral"),
                                amount=abs(float(gasto.get("amount", 0))),
                                type=gasto.get("type", "Debito")
                            ))
                        db.commit()
                    self.on_load() 
            except Exception as e:
                print(f"Erro no parse do JSON: {e}")

    def submit_message(self, form_data: dict):
        """Recebe os dados do formulário quando o usuário aperta Enter ou clica em Enviar."""
        # Extrai a mensagem pelo nome do input (chat_input)
        user_query = form_data.get("chat_input", "")
        
        if not user_query.strip():
            return

        historico_formatado = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in self.chat_history])

        # Salva msg do usuário
        self.chat_history.append({"role": "user", "content": user_query})
        with rx.session() as db:
            db.add(ChatMessage(role="user", content=user_query))
            db.commit()
            
        self.is_loading = True
        yield

        try:
            self.extract_transactions_from_text(user_query)
            
            agent = get_financial_advisor(
                financial_data=self.database_summary,
                chat_history=historico_formatado
            )
            response = agent.run(user_query)
            
            self.chat_history.append({"role": "agent", "content": response.content})
            with rx.session() as db:
                db.add(ChatMessage(role="agent", content=response.content))
                db.commit()
                
        except Exception as e:
            error_msg = f"Erro de comunicação: {str(e)}"
            self.chat_history.append({"role": "agent", "content": error_msg})
        
        self.is_loading = False

    def clear_chat(self):
        """Apaga o histórico do chat E as transações do banco de dados."""
        with rx.session() as db:
            db.query(ChatMessage).filter(ChatMessage.session_id == "default_user").delete()
            db.query(Transaction).filter(Transaction.session_id == "default_user").delete()
            db.commit()
        self.on_load()


# --- COMPONENTES VISUAIS ---
def message_bubble(message: dict) -> rx.Component:
    is_user = message["role"] == "user"
    return rx.box(
        rx.markdown(message["content"]),
        bg=rx.cond(is_user, "blue.100", "white"),
        color="black",
        padding="1em",
        border_radius="8px",
        margin_y="0.5em",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
        max_width="80%",
        box_shadow="0 2px 4px rgba(0,0,0,0.05)"
    )

def dashboard_panel() -> rx.Component:
    return rx.vstack(
        rx.heading("📊 Visão Geral", size="5"),
        rx.text("Distribuição de Gastos", color="gray"),
        
        rx.recharts.pie_chart(
            rx.recharts.pie(
                data=AdvisorState.chart_data,
                data_key="value",
                name_key="name",
                cx="50%",
                cy="50%",
                outer_radius=100,
                fill="#8884d8",
                label=True,
            ),
            rx.recharts.tooltip(),
            height=300,
            width="100%",
        ),
        
        rx.divider(),
        rx.upload(
            rx.vstack(
                rx.icon("upload", size=24),
                rx.text("Importar Extrato (CSV)", font_size="0.9em"),
                align_items="center",
                padding="1em",
                border="1px dashed #ccc",
                border_radius="8px",
                width="100%",
                _hover={"bg": "gray.50", "cursor": "pointer"}
            ),
            id="csv_upload",
            multiple=False,
            accept={"text/csv": [".csv"]},
            max_files=1,
            on_drop=AdvisorState.handle_upload(rx.upload_files(upload_id="csv_upload")),
        ),
        rx.cond(AdvisorState.is_uploading, rx.spinner(size="2")),
        
        width="100%",
        padding="1.5em",
        border="1px solid #eaeaea",
        border_radius="12px",
        bg="white"
    )

def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("💰 Assessor Financeiro Inteligente", size="8", margin_bottom="1em"),
            rx.hstack(
                # Coluna Esquerda: Dashboard (Reduzido para dar mais espaço ao chat)
                rx.box(dashboard_panel(), width="28%"),
                
                # Coluna Direita: Chat (Aumentado)
                rx.vstack(
                    rx.hstack(
                        rx.heading("Chat", size="5"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("trash-2", size=18),
                            "Zerar Dados",
                            on_click=AdvisorState.clear_chat,
                            color_scheme="red",
                            variant="soft",
                            size="2"
                        ),
                        width="100%",
                        align_items="center",
                        padding_bottom="0.5em"
                    ),
                    rx.scroll_area(
                        rx.vstack(
                            # Renderiza as mensagens do histórico
                            rx.foreach(AdvisorState.chat_history, message_bubble),
                            
                            # O novo balão de "Pensamento" que só aparece quando está processando
                            rx.cond(
                                AdvisorState.is_loading,
                                rx.box(
                                    rx.hstack(
                                        rx.spinner(size="2"),
                                        rx.text("Processando e consultando ferramentas...", color="gray", font_size="0.9em", font_style="italic"),
                                        spacing="3",
                                        align_items="center"
                                    ),
                                    bg="gray.50",
                                    padding="1em",
                                    border_radius="8px",
                                    margin_y="0.5em",
                                    align_self="flex-start",
                                    border="1px dashed #ccc"
                                )
                            ),
                            # Garante que a rolagem fique ancorada no final
                            padding_bottom="2em" 
                        ),
                        height="550px", # Aumentamos a altura da caixa de chat
                        width="100%",
                        border="1px solid #eaeaea",
                        padding="1.5em",
                        border_radius="12px",
                        background_color="#fafafa"
                    ),
                    
                    # O Formulário que permite usar a tecla Enter
                    rx.form(
                        rx.hstack(
                            rx.input(
                                name="chat_input", # Nome que o form_data vai capturar
                                placeholder="Ex: Gastei 150 no borracheiro...",
                                width="100%",
                                size="3"
                            ),
                            rx.button(
                                "Enviar", 
                                type="submit", # Transforma o botão num gatilho de submit
                                loading=AdvisorState.is_loading, 
                                size="3"
                            ),
                            width="100%"
                        ),
                        on_submit=AdvisorState.submit_message,
                        reset_on_submit=True,
                        width="100%"
                    ),
                    width="90%" 
                ),
                width="100%",
                align_items="start",
                spacing="6"
            )
        ),
        padding="2em",
        max_width="1400px" 
    )

app = rx.App()
app.add_page(index, on_load=AdvisorState.on_load)