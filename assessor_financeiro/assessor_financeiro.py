import reflex as rx
from .agent import get_financial_advisor

class AdvisorState(rx.State):
    """Estado global da aplicação."""
    
    finance_input: str = ""
    current_message: str = ""
    
    # Pré-carregamos o chat com a pergunta de onboarding do agente
    chat_history: list[dict[str, str]] = [
        {
            "role": "agent",
            "content": "Olá! 👋 Sou seu Assessor Financeiro Pessoal. Antes de olharmos para planilhas e números, quero entender o que é importante para você. **O que te faz feliz no tempo livre? Quais são seus hobbies ou projetos atuais?**"
        }
    ]
    is_loading: bool = False

    def set_finance_input(self, value: str):
        self.finance_input = value

    def set_current_message(self, value: str):
        self.current_message = value

    def submit_message(self):
        """Processa a mensagem do usuário e chama o agente AGNO."""
        if not self.current_message.strip():
            return

        user_query = self.current_message
        
        historico_formatado = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in self.chat_history]
        )

        self.chat_history.append({"role": "user", "content": user_query})
        self.current_message = ""
        self.is_loading = True
        yield  # Atualiza a UI para mostrar o loading

        try:
            # Não passamos mais o lifestyle_context
            agent = get_financial_advisor(
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
        max_width="80%",
        box_shadow="0 2px 4px rgba(0,0,0,0.05)"
    )

def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("💰 Assessor Financeiro Inteligente", size="8", margin_bottom="1em"),
            
            rx.hstack(
                # Coluna Esquerda: Apenas Gastos agora
                rx.vstack(
                    rx.heading("Base de Dados", size="5"),
                    rx.text("Cole seus gastos ou CSV sintético aqui para o agente ter contexto numérico:"),
                    rx.text_area(
                        placeholder="Ex: Aluguel R$ 1500, Mercado R$ 800...",
                        on_blur=AdvisorState.set_finance_input,
                        width="100%",
                        height="300px"
                    ),
                    width="35%",
                    padding="1.5em",
                    border="1px solid #eaeaea",
                    border_radius="12px",
                    bg="white"
                ),
                
                # Coluna Direita: Chat
                rx.vstack(
                    rx.heading("Chat", size="5"),
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(AdvisorState.chat_history, message_bubble),
                        ),
                        height="500px",
                        width="100%",
                        border="1px solid #eaeaea",
                        padding="1.5em",
                        border_radius="12px",
                        background_color="#fafafa"
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Responda ao agente...",
                            value=AdvisorState.current_message,
                            on_change=AdvisorState.set_current_message,
                            width="100%",
                            size="3"
                        ),
                        rx.button(
                            "Enviar",
                            on_click=AdvisorState.submit_message,
                            loading=AdvisorState.is_loading,
                            size="3"
                        ),
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
app.add_page(index)