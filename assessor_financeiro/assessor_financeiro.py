import reflex as rx
from .agent import get_financial_advisor

class AdvisorState(rx.State):
    """Estado global da aplicação."""
    
    # Inputs do usuário
    lifestyle_input: str = ""
    finance_input: str = ""
    current_message: str = ""
    
    # Histórico de chat no formato [{"role": "user/agent", "content": "..."}]
    chat_history: list[dict[str, str]] = []
    is_loading: bool = False

    # --- SETTERS EXPLÍCITOS (Adicione estas três funções) ---
    def set_lifestyle_input(self, value: str):
        self.lifestyle_input = value

    def set_finance_input(self, value: str):
        self.finance_input = value

    def set_current_message(self, value: str):
        self.current_message = value
    # ---------------------------------------------------------

    def submit_message(self):
        """Processa a mensagem do usuário e chama o agente AGNO."""
        if not self.current_message.strip():
            return

        # 1. Salva a pergunta atual na variável e limpa o input
        user_query = self.current_message
        
        # 2. Formata todo o histórico ANTERIOR em um texto para servir de memória
        historico_formatado = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in self.chat_history]
        )

        # 3. Adiciona a nova pergunta à interface visual do chat
        self.chat_history.append({"role": "user", "content": user_query})
        self.current_message = ""
        self.is_loading = True
        yield  # Atualiza a UI para mostrar o loading

        try:
            # 4. Injeta o histórico de conversas no agente
            agent = get_financial_advisor(
                lifestyle_context=self.lifestyle_input,
                financial_data=self.finance_input,
                chat_history=historico_formatado
            )
            
            response = agent.run(user_query)
            
            self.chat_history.append({"role": "agent", "content": response.content})
        except Exception as e:
            self.chat_history.append({"role": "agent", "content": f"Erro de comunicação: {str(e)}"})
        
        self.is_loading = False


# --- COMPONENTES VISUAIS ---

def message_bubble(message: dict) -> rx.Component:
    """Renderiza um balão de mensagem condicional (usuário ou agente)."""
    is_user = message["role"] == "user"
    return rx.box(
        rx.markdown(message["content"]),
        bg=rx.cond(is_user, "blue.100", "gray.100"),
        color="black",
        padding="1em",
        border_radius="8px",
        margin_y="0.5em",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
        max_width="80%"
    )

def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("💰 Assessor Financeiro Inteligente", size="8", margin_bottom="1em"),
            
            rx.hstack(
                # Coluna Esquerda: Contexto do Usuário
                rx.vstack(
                    rx.heading("1. Seu Perfil", size="5"),
                    rx.text("O que te faz feliz? (Hobbies, estilo de vida, projetos)"),
                    rx.text_area(
                        placeholder="Ex: Faço trilha com minha Motona aos finais de semana, gosto de sorvete e...",
                        on_blur=AdvisorState.set_lifestyle_input,
                        width="100%",
                        height="120px"
                    ),
                    
                    rx.heading("2. Seus Gastos", size="5", margin_top="1em"),
                    rx.text("Cole seus gastos ou CSV (Para os testes, use dados sintéticos do Faker!)"),
                    rx.text_area(
                        placeholder="Ex: Aluguel R$ 1500, Mercado R$ 800, Peças para Moto R$ 300...",
                        on_blur=AdvisorState.set_finance_input,
                        width="100%",
                        height="200px"
                    ),
                    width="40%",
                    padding="1em",
                    border="1px solid #eaeaea",
                    border_radius="8px"
                ),
                
                # Coluna Direita: Chat
                rx.vstack(
                    rx.heading("Chat com o Assessor", size="5"),
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(AdvisorState.chat_history, message_bubble),
                        ),
                        height="400px",
                        width="100%",
                        border="1px solid #eaeaea",
                        padding="1em",
                        border_radius="8px",
                        background_color="#fafafa"
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Pergunte sobre suas finanças...",
                            value=AdvisorState.current_message,
                            on_change=AdvisorState.set_current_message,
                            width="100%"
                        ),
                        rx.button(
                            "Enviar",
                            on_click=AdvisorState.submit_message,
                            loading=AdvisorState.is_loading
                        ),
                        width="100%"
                    ),
                    width="60%"
                ),
                width="100%",
                align_items="start",
                spacing="4"
            )
        ),
        padding="2em",
        max_width="1200px"
    )

app = rx.App()
app.add_page(index)