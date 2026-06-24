import reflex as rx
import os
from agente_financeiro import agente

class State(rx.State):  # pylint: disable=inherit-non-class
    """Gerencia o estado do chat e o upload do arquivo."""
    
    pergunta: str = ""
    historico: list[dict[str, str]] = []
    carregando: bool = False

    def set_pergunta(self, texto: str):
        self.pergunta = texto

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Salva a planilha enviada na pasta de dados do agente."""
        for file in files:
            upload_data = await file.read()
            os.makedirs("dados", exist_ok=True)
            
            # Salvamos exatamente no caminho que o agente procura
            caminho = "dados/extrato_sintetico.csv"
            with open(caminho, "wb") as f:
                f.write(upload_data)
                
        # Avisa o usuário no chat que deu certo
        self.historico.append({
            "role": "agente", 
            "texto": "✅ **Planilha carregada com sucesso!** Já tenho acesso aos seus dados. O que gostaria de analisar?"
        })
        yield

    def enviar_mensagem(self):
        if self.pergunta.strip() == "":
            return
            
        self.historico.append({"role": "usuario", "texto": self.pergunta})
        pergunta_atual = self.pergunta
        self.pergunta = ""
        self.carregando = True
        yield 
        
        try:
            resposta = agente.run(pergunta_atual).content 
        except Exception as e:
            resposta = f"Erro ao processar: {str(e)}"
            
        self.historico.append({"role": "agente", "texto": resposta})
        self.carregando = False


def mensagem_ui(mensagem: dict):
    """Estilo minimalista para as bolhas de mensagem."""
    eh_usuario = mensagem["role"] == "usuario"
    
    return rx.box(
        rx.markdown(mensagem["texto"]),
        bg=rx.cond(eh_usuario, rx.color("blue", 2), rx.color("gray", 2)),
        color=rx.cond(eh_usuario, rx.color("blue", 11), rx.color("gray", 11)),
        p="4",
        border_radius="xl",
        border=rx.cond(eh_usuario, f"1px solid {rx.color('blue', 4)}", f"1px solid {rx.color('gray', 4)}"),
        align_self=rx.cond(eh_usuario, "flex-end", "flex-start"),
        max_width="85%",
        box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    )

def index():
    """A página principal do Assessor."""
    return rx.container(
        rx.vstack(
            rx.heading("Assessor Financeiro Pessoal", size="8", margin_bottom="2"),
            rx.text("Envie seu extrato bancário para análise.", color="gray", margin_bottom="6"),
            
            # --- ÁREA DE UPLOAD ---
            rx.vstack(
                rx.upload(
                    rx.vstack(
                        rx.icon("upload", size=32, color=rx.color("gray", 11)),
                        rx.text("Arraste sua planilha .csv aqui ou clique para buscar", color=rx.color("gray", 11)),
                        align="center",
                        justify="center",
                        padding="4",
                    ),
                    id="upload_extrato",
                    multiple=False,
                    accept={"text/csv": [".csv"]},
                    border=f"2px dashed {rx.color('gray', 6)}",
                    border_radius="xl",
                    width="100%",
                    padding="2",
                    bg=rx.color("gray", 1),
                    _hover={"bg": rx.color("gray", 3)},
                    cursor="pointer",
                ),
                rx.button(
                    "Processar Planilha",
                    on_click=State.handle_upload(rx.upload_files(upload_id="upload_extrato")),
                    width="100%",
                    color_scheme="gray",
                    variant="surface",
                ),
                width="100%",
                spacing="2",
                margin_bottom="6"
            ),
            
            # --- ÁREA DO CHAT ---
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(State.historico, mensagem_ui),
                    spacing="4",
                    width="100%",
                ),
                height="50vh",
                width="100%",
                padding="6",
                border=f"1px solid {rx.color('gray', 4)}",
                border_radius="xl",
                bg="white",
                box_shadow="sm",
            ),
            
            # --- BARRA DE DIGITAÇÃO ---
            rx.hstack(
                rx.input(
                    placeholder="Pergunte sobre seus gastos...",
                    value=State.pergunta,
                    on_change=State.set_pergunta,
                    width="100%",
                    size="3",
                    radius="large",
                ),
                rx.button(
                    rx.icon("send", size=18),
                    "Enviar",
                    on_click=State.enviar_mensagem,
                    loading=State.carregando,
                    size="3",
                    radius="large",
                ),
                width="100%",
                margin_top="4"
            ),
            width="100%",
            max_width="700px",
            margin="0 auto",
            padding_y="8vh"
        )
    )

app = rx.App(
    theme=rx.theme(appearance="light", accent_color="blue", radius="large")
)
app.add_page(index)