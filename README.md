# agno-assessor-financeiro

Projeto de um assessor financeiro pessoal usando o framework AGNO.

## Uso do modelo local com OpenWebUI

Este projeto inclui uma configuração para executar o modelo localmente com Ollama e acessar via OpenWebUI.

### Requisitos

- Docker
- Docker Compose

### Como usar

1. Na raiz do projeto, inicie os containers:

    ```bash
    docker compose up -d
    ```

2. Aguarde o container `ollama` iniciar e carregar o modelo `llama3`.

3. Acesse a interface do OpenWebUI em:

    ```
    http://localhost:3000
    ```

### O que está configurado

- `docker-compose.yml`
  - `ollama`: container que roda o servidor Ollama e expõe a API em `11434`
  - `open-webui`: interface web que se conecta ao Ollama via `OLLAMA_BASE_URL=http://ollama:11434`

- `docker/Dockerfile-ollama`
  - usa a imagem oficial `ollama/ollama`
  - inicializa o Ollama no build para baixar o modelo `llama3`
  - expõe a porta `11434`

### Observações

- O OpenWebUI está configurado para abrir com o modelo padrão `llama3`.
- Se desejar reiniciar os containers:

    ```bash
    docker compose down
    docker compose up -d
    ```

- Se for necessário atualizar o modelo ou a imagem, recrie o container:

    ```bash
    docker compose build ollama
    docker compose up -d
    ```