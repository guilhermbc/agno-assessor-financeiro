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
    current_message: str = ""
    chat_history: list[dict[str, str]] = []
    chart_data: list[dict[str, any]] = []
    database_summary: str = "" # Texto resumido que o agente conselheiro vai ler
    
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
            
            # Recalcula o Gráfico e o Resumo para o Agente
            transactions = db.query(Transaction).filter(Transaction.session_id == "default_user").all()
            
            category_totals = {}
            total_gastos = 0
            for t in transactions:
                if t.type.lower() == "debito":
                    category_totals[t.category] = category_totals.get(t.category, 0) + abs(t.amount)
                    total_gastos += abs(t.amount)
            
            self.chart_data = [{"name": k, "value": v} for k, v in category_totals.items()]
            
            # Formata um resumo para o Llama ler
            self.database_summary = f"Total Gasto Registrado: R$ {total_gastos:.2f}\nDetalhamento:\n"
            for k, v in category_totals.items():
                self.database_summary += f"- {k}: R$ {v:.2f}\n"

    def set_current_message(self, value: str):
        self.current_message = value

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Lê o CSV real enviado pelo usuário e salva no Banco de Dados."""
        self.is_uploading = True
        yield
        try:
            file = files[0]
            upload_data = await file.read()
            df = pd.read_csv(io.BytesIO(upload_data))
            df.columns = df.columns.str.strip()
            
            with rx.session() as db:
                for _, row in df.iterrows():
                    # Trata o valor para ficar positivo no DB se for débito
                    valor = float(row.get("Valor", 0))
                    tipo = row.get("Tipo", "Debito").capitalize()
                    categoria = row.get("Descricao", "Outros")
                    
                    db.add(Transaction(category=categoria, amount=valor, type=tipo))
                db.commit()
                
            self.chat_history.append({"role": "agent", "content": "✅ **CSV processado e salvo no banco de dados!** O gráfico já foi atualizado."})
            self.on_load() # Atualiza UI
            
        except Exception as e:
            self.chat_history.append({"role": "agent", "content": f"Erro ao ler CSV: {str(e)}"})
            
        self.is_uploading = False
        yield

    def extract_transactions_from_text(self, text: str):
        """Passo 1 da Orquestração: Roda o Agente Extrator para pescar gastos do chat."""
        extractor = get_data_extractor_agent()
        response = extractor.run(text)
        
        # Garante que vai pegar apenas o JSON da resposta (evita falhas de formatação do LLM)
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
                    self.on_load() # Atualiza o gráfico em tempo real
            except Exception as e:
                print(f"Erro no parse do JSON: {e}")

    def submit_message(self):
        if not self.current_message.strip():
            return

        user_query = self.current_message
        historico_formatado = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in self.chat_history])

        # Salva msg do usuário
        self.chat_history.append({"role": "user", "content": user_query})
        with rx.session() as db:
            db.add(ChatMessage(role="user", content=user_query))
            db.commit()
            
        self.current_message = ""
        self.is_loading = True
        yield

        try:
            # 1. Agente Extrator avalia se há gastos novos e salva no DB
            self.extract_transactions_from_text(user_query)
            
            # 2. Agente Assessor lê o DB atualizado e responde ao usuário
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
        bg=rx.cond(is_user, "blue.100", "gray.100"),
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
        
        # Gráfico (agora 100% dinâmico)
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
        
        # Upload de CSV Real
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
                rx.box(dashboard_panel(), width="35%"),
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
                        rx.vstack(rx.foreach(AdvisorState.chat_history, message_bubble)),
                        height="500px",
                        width="100%",
                        border="1px solid #eaeaea",
                        padding="1.5em",
                        border_radius="12px",
                        background_color="#fafafa"
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Ex: Gastei 150 no borracheiro...",
                            value=AdvisorState.current_message,
                            on_change=AdvisorState.set_current_message,
                            width="100%",
                            size="3"
                        ),
                        rx.button("Enviar", on_click=AdvisorState.submit_message, loading=AdvisorState.is_loading, size="3"),
                        width="100%"
                    ),
                    width="65%"
                ),
                width="100%",
                align_items="start",
                spacing="6"
            )
        ),
        padding="2em",
        max_width="1200px"
    )

app = rx.App()
app.add_page(index, on_load=AdvisorState.on_load)