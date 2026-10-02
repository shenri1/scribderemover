# 📄 Scribd Downloader

Baixe documentos do Scribd como **PDF**, página por página, com uma janelinha simples ou direto pelo terminal. O arquivo sempre vai para a pasta **Downloads** do seu sistema.

![Python](https://img.shields.io/badge/python-3.14%2B-blue)
![uv](https://img.shields.io/badge/gerenciado%20com-uv-de5fe9)
![Navegadores](https://img.shields.io/badge/navegadores-Chrome%20%7C%20Edge%20%7C%20Firefox-orange)
![Sistemas](https://img.shields.io/badge/sistemas-Windows%20%7C%20Linux-lightgrey)

## ✨ Recursos

- 🖱️ **Interface gráfica** pequena, com barra de progresso e porcentagem do download
- ⌨️ **Modo terminal**, para quem prefere linha de comando
- 🌍 Aceita links de qualquer idioma do Scribd (`www`, `pt`, `es`, `de`...)
- 🔎 **Detecta sozinho** o navegador instalado: Chrome, Edge ou Firefox
- 📥 Salva sempre na pasta de **Downloads** do sistema, no Windows e no Linux
- 🧷 Nunca sobrescreve: se o arquivo já existir, vira `nome (1).pdf`
- 🧠 Exporta em lotes, para não estourar a memória em documentos grandes

## 📦 Requisitos

- [uv](https://docs.astral.sh/uv/)
- Um navegador: **Google Chrome**, **Microsoft Edge** (já vem no Windows) ou **Mozilla Firefox**
- Internet na primeira execução, porque o driver do navegador é baixado automaticamente
- Linux: o tkinter pode ser um pacote separado (`sudo apt install python3-tk`)

## 🚀 Como usar

```bash
# Clonar e entrar na pasta
git clone https://github.com/shenri1/scribderemover.git
cd scribderemover
```

**Com interface gráfica**

```bash
uv run app.py
```

Cole o link do documento, clique em **Download** e acompanhe a barra de progresso.

**No terminal**

```bash
uv run script.py
```

Exemplo de link aceito:

```
https://pt.scribd.com/document/123456789/Titulo-Do-Documento
```

## ⚙️ Configuração (opcional)

Tudo é ajustável por variáveis de ambiente:

| Variável | Padrão | O que faz |
|---|---|---|
| `SCRIBD_BROWSER` | automático | Força `chrome`, `edge` ou `firefox` |
| `SCRIBD_HEADLESS` | `1` | `0` abre o navegador visível, útil para depuração |
| `SCRIBD_EXPORT_BATCH_SIZE` | `8` | Páginas carregadas por lote |
| `SCRIBD_PAGE_LOAD_TIMEOUT` | `120` | Segundos para um lote carregar |
| `SCRIBD_CDP_TIMEOUT` | `600` | Segundos de espera por comando do driver |

No PowerShell:

```powershell
$env:SCRIBD_BROWSER = "firefox"
uv run app.py
```

## 🧩 Como funciona

1. O link é convertido para a versão *embed* do documento.
2. Um navegador sem janela abre a página, remove banners e barras de ferramentas e carrega as páginas por lote.
3. Cada página é isolada e impressa em PDF no tamanho exato dela.
4. Os PDFs de página são juntados em um único arquivo na pasta Downloads.

## 🗂️ Estrutura

```
app.py              entrada da interface gráfica
script.py           entrada do terminal
downloader/
  browsers.py       detecta e abre Chrome / Edge / Firefox
  config.py         configurações (variáveis SCRIBD_*)
  exporter.py       exportação página por página
  gui.py            janela com barra de progresso (tkinter)
  cli.py            modo terminal
  paths.py          URL, nome do arquivo e pasta de Downloads
  scripts.py        JavaScript injetado na página
```

## 🪟 Gerar um `.exe` (Windows)

```bash
uv add --dev pyinstaller
uv run pyinstaller --onefile --windowed --name ScribdDownloader app.py
```

O executável fica em `dist/ScribdDownloader.exe`. O navegador continua sendo necessário na máquina.

## ⚠️ Aviso

Use apenas com documentos que você tem direito de baixar e respeitando os termos de uso do Scribd e os direitos autorais dos autores. Este projeto é para uso pessoal e educacional.
