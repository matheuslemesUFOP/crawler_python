# Crawler Python

Crawler em Python utilizando Selenium, Beautiful Soup e Pandas para extração e tratamento de dados da web.

## Pré-requisitos

- **Python** — versão **3.11** ou superior
- **pip** — gerenciador de pacotes do Python (já vem com a instalação oficial do Python)

### Verificar instalação

```bash
python3 --version   # ou: python --version
pip --version       # ou: pip3 --version
```

### Instalar Python 3.11 e pip

**Linux (Debian/Ubuntu):**

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

O `python3-pip` costuma instalar o pip para a versão padrão do Python. Se quiser `pip` associado ao 3.11:

```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 -
```

**macOS:**

```bash
# Com Homebrew (https://brew.sh)
brew install python@3.11
```

O Homebrew já inclui o pip. Use `python3.11` e `pip3.11` no terminal.

**Windows:**

1. Acesse [python.org/downloads](https://www.python.org/downloads/) e baixe o instalador do **Python 3.11**.
2. Execute o instalador e marque **"Add Python to PATH"**.
3. Na mesma tela, escolha **"Install pip"** (já vem marcado por padrão).
4. Conclua a instalação e reinicie o terminal. Teste com `python --version` e `pip --version`.

---

## Configuração do Poetry

O projeto usa [Poetry](https://python-poetry.org/) para gerenciamento de dependências e ambiente virtual.

### Instalar o Poetry

**Opção 1 — Via instalador oficial (recomendado):**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Depois, adicione o Poetry ao `PATH` (o instalador costuma mostrar o comando; no Linux/macOS é comum):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Para tornar permanente, adicione a linha acima ao `~/.bashrc` ou `~/.zshrc`.

**Opção 2 — Via pipx (ambiente isolado):**

```bash
# Instalar pipx (se não tiver)
pip install --user pipx
pipx ensurepath

# Instalar Poetry com Python 3.11+
pipx install poetry --python python3.11
```

### Configurar o Poetry

**Definir Python 3.11 como padrão do projeto**

O projeto está configurado para usar Python 3.11. Para garantir que o ambiente virtual use essa versão (recomendado após clonar ou ao ter várias versões instaladas):

```bash
poetry env use python3.11
```

Esse comando define o interpretador padrão do projeto e recria o ambiente virtual com Python 3.11, se necessário. Em seguida, rode `poetry install` para instalar as dependências.

Configurações úteis (opcionais):

```bash
# Criar o venv dentro da pasta do projeto (.venv)
poetry config virtualenvs.in-project true

# Não perguntar por credenciais de repositório
poetry config keyring.enabled false
```

### Comandos básicos

| Comando | Descrição |
|--------|-----------|
| `poetry install` | Cria o ambiente virtual e instala todas as dependências |
| `poetry add <pacote>` | Adiciona uma dependência ao projeto |
| `poetry run python script.py` | Executa um script no ambiente do projeto |
| `poetry shell` | Ativa o ambiente virtual no terminal atual |

---

## Executando o projeto

1. **Clone ou acesse o repositório:**

   ```bash
   cd crawler_python
   ```

2. **Instale as dependências com o Poetry:**

   ```bash
   poetry install
   ```

3. **Ative o ambiente (opcional) e execute seus scripts:**

   ```bash
   poetry shell
   python seu_script.py
   ```

   Ou sem ativar o shell:

   ```bash
   poetry run python seu_script.py
   ```

---

## Dependências principais

- **Selenium** — automação de navegador para páginas dinâmicas
- **Beautiful Soup** — parsing de HTML/XML
- **Pandas** — manipulação e análise de dados

Todas estão declaradas no `pyproject.toml` e são instaladas com `poetry install`.
