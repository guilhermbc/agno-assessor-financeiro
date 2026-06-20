import reflex as rx
import asyncio

# --- ESTADO DA APLICAÇÃO ---
class ChatState(rx.State):
    # Lista de tuplas (Mensagem, É_IA?)
    messages: list[tuple[str, bool]] = [
        ("Olá! Sou o seu assessor financeiro. Como posso ajudar seu patrimônio hoje?", True)
    ]
    current_message: str = ""
    is_loading: bool = False

    @rx.event
    def mudar_mensagem(self, texto: str):
        """Atualiza o valor da mensagem atual conforme o usuário digita."""
        self.current_message = texto

    @rx.event
    def tratar_teclado(self, key: str):
        if key == "Enter":
            return ChatState.send_message

    @rx.event
    async def send_message(self):
        if not self.current_message:
            return

        # Adiciona pergunta do usuário
        self.messages.append((self.current_message, False))
        user_q = self.current_message
        self.current_message = ""
        self.is_loading = True
        yield

        # Simulação de processamento da IA
        await asyncio.sleep(1.5)
        
        resposta = f"Analisando o mercado para '{user_q}'... Minha recomendação estratégica baseada em seu perfil conservador seria diversificar 15% em ativos atrelados ao IPCA e manter liquidez em fundos DI."
        
        self.messages.append((resposta, True))
        self.is_loading = False

# # --- ESTADO DA APLICAÇÃO ---
# class ChatState(rx.State):
#     # Lista de tuplas (Mensagem, É_IA?)
#     messages: list[tuple[str, bool]] = [
#         ("Olá! Sou o Agno, seu assessor financeiro IA. Como posso ajudar seu patrimônio hoje?", True)
#     ]
#     current_message: str = ""
#     is_loading: bool = False

#     @rx.event
#     async def send_message(self):
#         if not self.current_message:
#             return

#         # Adiciona pergunta do usuário
#         self.messages.append((self.current_message, False))
#         user_q = self.current_message
#         self.current_message = ""
#         self.is_loading = True
#         yield

#         # Simulação de processamento da IA
#         await asyncio.sleep(1.5)
        
#         # Resposta mockada (Aqui você integraria com OpenAI/LangChain)
#         resposta = f"Analisando o mercado para '{user_q}'... Minha recomendação estratégica baseada em seu perfil conservador seria diversificar 15% em ativos atrelados ao IPCA e manter liquidez em fundos DI."
        
#         self.messages.append((resposta, True))
#         self.is_loading = False


# --- COMPONENTES DE INTERFACE ---

# def message_bubble(content: str, is_ai: bool):
#     """Estiliza as bolhas de chat."""
#     return rx.box(
#         rx.text(
#             content,
#             color="white" if is_ai else "#e2e8f0",
#             font_size="15px",
#         ),
#         bg="#1e293b" if not is_ai else "linear-gradient(135deg, #064e3b 0%, #022c22 100%)",
#         padding="15px",
#         border_radius="15px",
#         border=rx.cond(is_ai, "1px solid #10b981", "1px solid #334155"),
#         margin_y="10px",
#         max_width="80%",
#         align_self="flex-start" if is_ai else "flex-end",
#     )
def message_bubble(content: str, is_ai: rx.Var):
    """Estiliza as bolhas de chat usando rx.cond para lógica de estilo."""
    return rx.box(
        rx.text(
            content,
            # Correção do Erro: Usa rx.cond no lugar do 'if/else' do Python
            color=rx.cond(is_ai, "white", "#e2e8f0"),
            font_size="15px",
        ),
        # Correção do Erro: Também usamos rx.cond para o background e bordas
        bg=rx.cond(
            is_ai, 
            "linear-gradient(135deg, #064e3b 0%, #022c22 100%)", 
            "#1e293b"
        ),
        padding="15px",
        border_radius="15px",
        border=rx.cond(
            is_ai, 
            "1px solid #10b981", 
            "1px solid #334155"
        ),
        margin_y="10px",
        max_width="80%",
        align_self=rx.cond(is_ai, "flex-start", "flex-end"),
    )

def sidebar():
    """Barra lateral esquerda."""
    return rx.vstack(
        rx.heading("Assessoria Financeira", color="#10b981", size="6", margin_bottom="20px", width="100%", text_align="center"),
        rx.button(
            rx.icon("plus", size=16), "Novo Chat", 
            width="100%", variant="outline", color_scheme="mint"
        ),
        rx.spacer(),
        rx.vstack(
            rx.text("Histórico Recente", color="#64748b", font_size="12px", width="100%"),
            rx.button("Análise Carteira Q3", variant="ghost", width="100%", justify_content="start", font_size="14px"),
            rx.button("Dúvida Tesouro Direto", variant="ghost", width="100%", justify_content="start", font_size="14px"),
            align_items="start",
            width="100%",
        ),
        padding="20px",
        width="260px",
        height="100vh",
        bg="#0f172a",
        border_right="1px solid #1e293b",
    )

def chat_interface():
    """Área principal de mensagens."""
    return rx.vstack(
        # Header do Chat
        rx.hstack(
            rx.badge("Online", color_scheme="mint", variant="soft"),
            rx.text("Assessoria Estratégica Ativa", color="#94a3b8"),
            width="100%",
            padding="20px",
            border_bottom="1px solid #1e293b",
        ),
        # Área de Mensagens (Scrollable)
        rx.box(
            rx.vstack(
                rx.foreach(ChatState.messages, lambda msg: message_bubble(msg[0], msg[1])),
                width="100%",
            ),
            overflow_y="auto",
            flex="1",
            padding="20px",
            width="100%",
        ),
        # Input de Texto
        rx.box(
            rx.hstack(
                rx.input(
                    placeholder="Pergunte sobre investimentos, taxas ou mercado...",
                    value=ChatState.current_message,
                    on_change=ChatState.mudar_mensagem,
                    on_key_down=ChatState.tratar_teclado,
                    bg="white",
                    border="none",
                    color="mint",
                    _focus={"border": "1px solid #10b981"},
                    height="50px",
                    width="100%",
                ),
                rx.button(
                    rx.cond(ChatState.is_loading, rx.spinner(size="1"), rx.icon("send")),
                    on_click=ChatState.send_message,
                    bg="#10b981",
                    color="white",
                    _hover={"bg": "#059669"},
                    height="50px",
                ),
                width="100%",
                max_width="800px",
                padding="20px",
            ),
            width="100%",
            display="flex",
            justify_content="center",
            bg="#0f172a",
        ),
        height="100vh",
        flex="1",
        bg="#0a0f1e",
    )

# --- PÁGINA PRINCIPAL ---

def index() -> rx.Component:
    return rx.hstack(
        sidebar(),
        chat_interface(),
        spacing="0",
        width="100%",
        height="100vh",
    )

app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="mint")
)
app.add_page(index, title="Assessor Financeiro")