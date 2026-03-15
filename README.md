# 🎮 Análise de Sentimento — GTA (Rockstar Games)

> Pipeline automatizado de scraping, análise de sentimento e geração de relatórios sobre avaliações do GTA, utilizando IA via API da Maritaca.

---

## 📌 Sobre o Projeto

Este projeto realiza a coleta automática de avaliações do GTA publicadas online, aplica análise de sentimento com o modelo de linguagem da **Maritaca AI** e gera relatórios estruturados com os resultados. O objetivo é entender a percepção dos jogadores sobre o jogo com base em dados reais.

---

## 🗂️ Estrutura do Projeto
```
AnaliseSentimentoGTA/
├── app.py              # Ponto de entrada principal — orquestra o pipeline
├── scraper.py          # Coleta e extração de avaliações (web scraping)
├── sentiment.py        # Análise de sentimento via API Maritaca
├── report.py           # Geração de relatório com os resultados
├── requirements.txt    # Dependências do projeto
├── .env                # Variáveis de ambiente (chave de API)
├── avaliacoes_gta.csv  # Dataset com avaliações coletadas
└── temp_gta.csv        # Arquivo temporário gerado durante o processamento
```

---

## 🚀 Como Executar

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/AnaliseSentimentoGTA.git
cd AnaliseSentimentoGTA
```

### 2. Crie e ative um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
```env
MARITACA_API_KEY=sua_chave_aqui
```

> ⚠️ **Nunca compartilhe sua chave de API publicamente. Adicione `.env` ao `.gitignore`.**

### 5. Execute o projeto
```bash
python app.py
```

---

## ⚙️ Fluxo do Pipeline
```
scraper.py  →  avaliacoes_gta.csv  →  sentiment.py  →  report.py
  (coleta)         (armazenamento)       (análise IA)    (relatório)
```

1. **`scraper.py`** — Realiza o scraping das avaliações e salva em `avaliacoes_gta.csv`
2. **`sentiment.py`** — Lê o CSV, envia cada avaliação para a API da Maritaca e classifica o sentimento (positivo, negativo ou neutro)
3. **`report.py`** — Consolida os resultados e gera um relatório final
4. **`app.py`** — Orquestra todas as etapas acima

---

## 🧰 Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python 3.13 | Linguagem principal |
| Maritaca AI | Modelo de linguagem para análise de sentimento |
| Requests / BeautifulSoup | Web scraping |
| Pandas | Manipulação de dados CSV |
| python-dotenv | Gerenciamento de variáveis de ambiente |

---

## 📋 Pré-requisitos

- Python 3.10+
- Chave de API válida da [Maritaca AI](https://maritaca.ai)
- Conexão com a internet (para scraping e chamadas à API)

---

## 🔒 Segurança

- Nunca exponha sua `MARITACA_API_KEY` em commits ou repositórios públicos
- O arquivo `.env` deve estar sempre listado no `.gitignore`
```gitignore
.env
__pycache__/
*.csv
venv/
```

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

Sofia Bueris Netto de Souza – RM565818
Vinícius Adrian Siqueira de Oliveira – RM564962
Augusto Oliveira Codo de Sousa – RM562080
Felipe de Oliveira Cabral – RM561720
Gabriel Tonelli Avelino Dos Santos – RM564705

