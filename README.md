# 🥷 LitisDoc

**LitisDoc** é o canivete suíço definitivo para manipulação avançada de arquivos PDF no Linux. Desenvolvido com foco em produtividade para advogados, auditores e profissionais que lidam com grandes volumes de documentos, o LitisDoc permite realizar operações complexas em arquivos (como conversões judiciais, assinaturas, quebra de senhas, e OCR) através de uma interface interativa no terminal extremamente fácil de usar.

---

## ✨ Funcionalidades

O LitisDoc consolida ferramentas poderosas (QPDF, Ghostscript, Poppler, OCRmyPDF, ReportLab) em uma interface central unificada.

### 🔄 Operações em Lote
*   **Gerador de Dossiês (Com Pré-Referenciação Hash):** Junte múltiplos PDFs e Imagens bagunçados em um Dossiê impecável. O sistema cria uma capa elegante com **Sumário (TOC)** automático, centraliza qualquer anexo em folhas A4 padronizadas, injeta *Bookmarks* de navegação, e insere uma **Hash Criptográfica Curta** (ex: `A7F92B...`) em todas as páginas, permitindo que você cite os anexos na sua petição com precisão cirúrgica antes mesmo do protocolo no PJe.
*   **Juntar PDFs (Merge):** Selecione múltiplos PDFs de uma pasta e funda todos eles em um único arquivo, escolhendo a ordem desejada.
*   **Imagens para PDF:** Converta múltiplos arquivos `.jpg` e `.png` diretamente para um arquivo PDF unificado.

### 🛡️ Segurança e Privacidade
*   **Proteger com Senha:** Criptografe seus arquivos confidenciais usando algoritmo AES de 256 bits.
*   **Remover Senha (Desbloquear):** Remova a senha de abertura de PDFs conhecidos para não precisar digitá-la repetidamente.
*   **Limpar Metadados (Anonimização):** Zere rastros de autoria, software de criação, localização e datas, garantindo o anonimato do documento.
*   **Marca D'água:** Insira textos (como "CONFIDENCIAL", "RASCUNHO") de ponta a ponta no documento de forma transparente.

### 🏛️ Adequação Jurídica / Processual
*   **Assinatura Digital (Token A3 / ICP-Brasil):** Assine seus PDFs usando tokens físicos ou smartcards com uma estrutura criptográfica perfeitamente compatível com a validação do ITI (Governo Brasileiro). Suporta múltiplas assinaturas no mesmo documento, diferentes estilos visuais, e inserção de **Carimbo de Tempo (TSA - PAdES)** para atestar a data/hora irrefutável.
*   **Verificador de Assinaturas:** Analise e dissecque as assinaturas digitais contidas em qualquer PDF usando o `pdfsig` nativo, identificando quem assinou, verificando a integridade da criptografia e validando Carimbos de Tempo (RFC 3161) integrados.
*   **Paginação Sequencial (Bates Stamping):** Numere páginas automaticamente (ex: "Fl. 01", "Fl. 02") no canto inferior direito para organização de processos e anexos.
*   **Converter para PDF/A:** Transforme documentos comuns no padrão internacional de Arquivamento de Longo Prazo, exigido por sistemas como **PJe** e **e-SAJ**, embutindo todas as fontes e garantindo conformidade.
*   **Comparar com outro PDF (Diff):** Compare duas minutas de contrato! O app gera um arquivo destacando as diferenças visuais (adicionadas ou removidas) entre a versão 1 e a versão 2.

### 🛠️ Modificações Físicas
*   **Extrair / Separar Páginas:** Extraia apenas as páginas que importam ditando os intervalos (ex: `1-5, 10, 15-20`).
*   **Reordenar Páginas:** Inverta ou embaralhe páginas inteiras (ex: digite `3,2,1` para inverter a ordem).
*   **Otimização para Web (Linearização):** Reestruture o PDF para que a 1ª página abra instantaneamente no navegador enquanto o resto baixa em segundo plano (Fast Web View).
*   **Rotacionar:** Gire páginas invertidas em +90º, -90º ou 180º.
*   **Compressão:** Reduza drasticamente o tamanho do arquivo para conseguir enviá-lo por e-mail ou anexá-lo em sistemas judiciais. Níveis disponíveis: `screen` (Mínimo), `ebook`, `printer` e `prepress`.

### 🔍 Extração e Inteligência
*   **Busca em Lote (Regex):** Pesquise por textos exatos ou padrões complexos (Expressões Regulares, ex: CPFs ou CNPJs) em todos os PDFs de uma pasta simultaneamente.
*   **Aplicar OCR:** Transforme PDFs "mortos" (imagens escaneadas) em documentos com texto pesquisável e selecionável.
*   **Renderizar para Imagens:** Transforme cada página do seu PDF em um `.jpg` independente (útil quando tribunais recusam formatos de texto).
*   **Extrair Texto:** Retire apenas o texto bruto do documento preservando o layout original.
*   **Extrair Imagens:** Varra o PDF e salve apenas as fotos e logos contidos dentro dele.

---

## ⚙️ Pré-requisitos (Debian / Ubuntu)

O **LitisDoc** faz o trabalho pesado orquestrando as melhores ferramentas de sistema do Linux. Antes de rodá-lo, você precisará ter essas dependências instaladas no seu sistema:

Abra seu terminal e rode o seguinte comando:
```bash
sudo apt update
sudo apt install -y poppler-utils qpdf ghostscript ocrmypdf tesseract-ocr tesseract-ocr-por diff-pdf-wx icc-profiles-free
```

*Nota: A ferramenta `pdfsig` utilizada no Verificador de Assinaturas já vem inclusa no pacote `poppler-utils`. Para utilizar a funcionalidade de Assinatura com Token A3, certifique-se de que o middleware/driver do seu token (como SafeSign, OpenSC ou Safenet) está devidamente instalado no sistema operacional.*

## 🚀 Instalação

A aplicação é modular e gerida pelo Python via `pip`. Recomenda-se criar um ambiente virtual (venv) na pasta do projeto.

1. Clone ou extraia o repositório do projeto.
2. Crie e ative o ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instale o LitisDoc em modo editável com as dependências do `pyproject.toml`:
   ```bash
   pip install -e .
   ```

*(Dependências Python incluídas automaticamente no `pyproject.toml`)*.

---

## 💻 Como Usar

O LitisDoc opera em **Modo Interativo (TUI)** de forma padrão. Basta iniciar o aplicativo e usar as setas do teclado para navegar.

### Rodando o App
Dentro da pasta do projeto com o `venv` ativado, basta digitar:
```bash
litisdoc
```

**Passo a passo no app:**
1. O aplicativo pedirá que você "Cole ou digite o caminho da pasta onde estão os PDFs".
2. Ele listará todas as opções de lote e todos os arquivos disponíveis na pasta.
3. Use as **setas do teclado** para selecionar o arquivo e aperte **Enter**.
4. Selecione a operação desejada no menu. 
5. O resultado sempre será salvo de forma segura dentro de uma subpasta chamada `/operações em pdfs/`, preservando seu documento original intacto.

### Atalho de Área de Trabalho (Desktop Entry)
Para facilitar ainda mais, você pode criar um atalho `.desktop` para rodá-lo com um clique.
```ini
[Desktop Entry]
Version=1.0
Name=LitisDoc
Comment=O Canivete Suíço de PDFs
Exec=gnome-terminal -- bash -c "cd '/caminho/do/litisdoc' && source venv/bin/activate && litisdoc; exec bash"
Icon=/caminho/do/litisdoc/litisdoc_icon.png
Terminal=false
Type=Application
Categories=Office;Utility;
```

---

## 📚 Tecnologias e Bibliotecas Utilizadas

O LitisDoc não reinventa a roda, mas sim atua como um maestro, orquestrando e unificando as melhores ferramentas de código-aberto disponíveis para PDF em uma única interface inteligente. Os créditos das operações vão para os seguintes projetos incríveis:

**Ferramentas de Sistema (Linux):**
*   **QPDF:** Motor veloz e estrutural para reordenação, separação, junção, encriptação e linearização.
*   **Poppler (poppler-utils):** Extração de texto, renderização (`pdftocairo`) e validação de assinaturas nativa (`pdfsig`).
*   **Ghostscript:** Motor robusto responsável por comprimir e otimizar vetores e imagens do PDF.
*   **OCRmyPDF & Tesseract OCR:** Conversão de imagens em textos pesquisáveis e conformidade PDF/A.
*   **diff-pdf-wx:** Comparação visual de camadas de PDFs.

**Bibliotecas Python:**
*   **PyHanko & python-pkcs11:** As estrelas por trás da funcionalidade de Assinatura Digital, responsáveis por empacotar a criptografia ASN.1 e comunicar diretamente com o hardware (Tokens A3 / Smartcards).
*   **pypdf:** Manipulação em baixo nível, limpeza de metadados e scrubbing.
*   **ReportLab:** Criação vetorial de Marcas d'água, Carimbos Visuais e Bates Stamping.
*   **img2pdf:** Conversor *lossless* (sem perdas) que injeta imagens nativamente nas páginas do PDF.
*   **Rich, Typer & Questionary:** O trio de ouro responsável por construir toda essa interface colorida, amigável e interativa diretamente no seu terminal.

---

## 📁 Estrutura do Projeto

A arquitetura do projeto foi desenhada para manter os "motores" (backends) completamente isolados da interface com o usuário, facilitando manutenções futuras.

```text
litisdoc/
├── pyproject.toml              # Arquivo de configuração de dependências
├── litisdoc/
│   ├── __init__.py
│   ├── cli.py                  # Entrypoint de comando
│   ├── tui.py                  # Lógica de Interface Textual Interativa (Questionary)
│   ├── core/
│   │   ├── deps.py             # Verificadores de dependências de sistema
│   │   └── executor.py         # Tratamento de subprocessos
│   └── backends/               # Wrappers das ferramentas de sistema
│       ├── diff.py             # (Comparador diff-pdf-wx)
│       ├── dossier.py          # (Gerador de Dossiês A4 com Pré-Referenciação Hash)
│       ├── ghostscript.py      # (Compressão)
│       ├── img2pdf.py          # (Conversão JPG -> PDF)
│       ├── metadata.py         # (Limpeza de propriedades com pypdf)
│       ├── ocrmypdf.py         # (Inteligência OCR e PDF/A)
│       ├── poppler.py          # (Extração e pdftocairo)
│       ├── qpdf.py             # (Lotes, Reordenação, Criptografia, Linearização)
│       ├── sign.py             # (Integração PKCS#11 e PyHanko para Assinaturas A3)
│       ├── verify.py           # (Validador de Assinaturas usando pdfsig)
│       └── watermark.py        # (Reportlab Paginação e Marca D'água)
```

## 📝 Licença
Desenvolvido para ambiente GNU/Linux. Sinta-se livre para modificar e adaptar este código às necessidades da sua rotina de trabalho.
