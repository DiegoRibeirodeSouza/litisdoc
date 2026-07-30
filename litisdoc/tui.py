import questionary
from pathlib import Path
from rich.console import Console
import sys
import os

from litisdoc.backends.ghostscript import compress_pdf
from litisdoc.backends.poppler import extract_text, extract_images, get_info, render_to_images
from litisdoc.backends.qpdf import merge_pdfs, split_pdf, rotate_pdf, encrypt_pdf, decrypt_pdf, linearize_pdf
from litisdoc.backends.ocrmypdf import apply_ocr, convert_to_pdfa
from litisdoc.backends.img2pdf import convert_images_to_pdf
from litisdoc.backends.metadata import clear_metadata
from litisdoc.backends.watermark import add_watermark, add_pagination
from litisdoc.backends.diff import compare_pdfs
from litisdoc.backends.sign import sign_with_a3
from litisdoc.backends.imposition import create_booklet
from litisdoc.backends.resurrect import scrub_pdf
from litisdoc.backends.search import search_in_pdfs
from litisdoc.backends.verify import verify_signatures

console = Console()

def run_tui():
    console.print("\n[bold green]=== Bem-vindo ao LitisDoc Interativo ===[/bold green]\n")
    
    while True:
        # Pede uma pasta ou arquivo sem valor preenchido por padrão
        target_path_str = questionary.path(
            "Cole ou digite o caminho da pasta ou do arquivo PDF:",
            default="",
            only_directories=False
        ).ask()
        
        if target_path_str is None: # Usuário cancelou (Ctrl+C)
            break
            
        # Limpa possíveis aspas que vêm do arrastar e soltar no terminal
        target_path_str = target_path_str.strip().strip("'\"")
        target_path = Path(target_path_str)
        
        if not target_path.exists():
            console.print("[bold red]Erro:[/bold red] Caminho não encontrado.")
            continue
            
        if target_path.is_file():
            is_pdf = False
            if target_path.suffix.lower() == '.pdf':
                is_pdf = True
            else:
                try:
                    with open(target_path, 'rb') as f:
                        if f.read(5) == b'%PDF-':
                            is_pdf = True
                except Exception:
                    pass
            
            if not is_pdf:
                console.print("[bold red]Erro:[/bold red] O arquivo selecionado não é um PDF válido.")
                continue
            target_dir = target_path.parent
            single_file_mode = True
        else:
            target_dir = target_path
            single_file_mode = False
            
        # Construir menu da pasta
        while True:
            # Re-lista PDFs pois podem ter novos
            pdfs = list(target_dir.glob("*.pdf"))
            
            if single_file_mode:
                selected_item = f"📄 {target_path.name}"
            else:
                pdf_choices = []
                
                # Opções de Lote
                if pdfs:
                    pdf_choices.append("🛠️  [LOTE] Juntar PDFs desta pasta")
                    pdf_choices.append("🔍  [LOTE] Buscar texto em PDFs desta pasta")
                    pdf_choices.append("🖋️  [LOTE] Assinar PDFs desta pasta com Token A3")
                    
                imgs = list(target_dir.glob("*.jpg")) + list(target_dir.glob("*.png")) + list(target_dir.glob("*.jpeg"))
                if imgs:
                    pdf_choices.append("🖼️  [LOTE] Converter Imagens desta pasta para PDF")
                    
                if pdfs or imgs:
                    pdf_choices.append("📑  [LOTE] Gerar Dossiê A4 (Padronizado c/ Capa)")
                    
                pdf_choices.append("--- Escolha um PDF abaixo para manipular ---")
                for p in pdfs:
                    pdf_choices.append(f"📄 {p.name}")
                    
                pdf_choices.append("<- Escolher outra pasta ou arquivo")
                pdf_choices.append("Sair")
                
                selected_item = questionary.select(
                    "Menu Principal:",
                    choices=pdf_choices,
                    use_indicator=True
                ).ask()
                
                if selected_item is None or selected_item == "<- Escolher outra pasta ou arquivo":
                    break
                    
                if selected_item == "Sair":
                    sys.exit(0)
                    
                if selected_item == "--- Escolha um PDF abaixo para manipular ---":
                    continue
                
            ops_dir = target_dir / "operações em pdfs"
            ops_dir.mkdir(exist_ok=True)
            
            if not single_file_mode:
                if selected_item == "🛠️  [LOTE] Juntar PDFs desta pasta":
                    # Rotina para juntar arquivos selecionados
                    pdf_names = [p.name for p in pdfs]
                    selected_to_merge = questionary.checkbox(
                        "Selecione os PDFs para juntar (na ordem desejada, use Espaço para marcar):",
                        choices=pdf_names
                    ).ask()
                    
                    if selected_to_merge and len(selected_to_merge) > 1:
                        out_name = questionary.text("Nome do arquivo final:", default="unificado.pdf").ask()
                        if out_name:
                            out_path = ops_dir / out_name
                            input_paths = [target_dir / p for p in selected_to_merge]
                            merge_pdfs(out_path, input_paths)
                    else:
                        console.print("[yellow]Selecione pelo menos 2 PDFs para juntar.[/yellow]")
                    continue
                    
                if selected_item == "🖼️  [LOTE] Converter Imagens desta pasta para PDF":
                    img_names = [p.name for p in imgs]
                    selected_imgs = questionary.checkbox(
                        "Selecione as imagens para converter (use Espaço):",
                        choices=img_names
                    ).ask()
                    
                    if selected_imgs:
                        out_name = questionary.text("Nome do PDF final:", default="imagens.pdf").ask()
                        if out_name:
                            out_path = ops_dir / out_name
                            input_paths = [target_dir / p for p in selected_imgs]
                            convert_images_to_pdf(out_path, input_paths)
                    continue

                if selected_item == "📑  [LOTE] Gerar Dossiê A4 (Padronizado c/ Capa)":
                    all_files = [p.name for p in pdfs] + [p.name for p in imgs]
                    selected_for_dossier = questionary.checkbox(
                        "Selecione os arquivos para o Dossiê (use Espaço para marcar):",
                        choices=all_files
                    ).ask()
                    
                    if selected_for_dossier:
                        title = questionary.text("Título da Capa do Dossiê:", default="DOCUMENTOS").ask()
                        out_name = questionary.text("Nome do arquivo final:", default="dossie.pdf").ask()
                        if title and out_name:
                            out_path = ops_dir / out_name
                            input_paths = [target_dir / p for p in selected_for_dossier]
                            from litisdoc.backends.dossier import create_dossier
                            create_dossier(title, input_paths, out_path)
                    continue

                if selected_item == "🔍  [LOTE] Buscar texto em PDFs desta pasta":
                    search_type = questionary.select(
                        "Qual tipo de busca deseja realizar?",
                        choices=["Busca Simples (Texto exato)", r"Busca Avançada (Regex Ex: \d{3}\.\d{3}\.\d{3}-\d{2})"]
                    ).ask()
                    if search_type:
                        use_regex = "Regex" in search_type
                        query = questionary.text("Digite o texto ou padrão a ser buscado:").ask()
                        if query:
                            search_in_pdfs(target_dir, query, use_regex)
                    continue

                if selected_item == "🖋️  [LOTE] Assinar PDFs desta pasta com Token A3":
                    pdf_names = [p.name for p in pdfs]
                    selected_to_sign = questionary.checkbox(
                        "Selecione os PDFs para assinar (use Espaço):",
                        choices=pdf_names
                    ).ask()
                    
                    if selected_to_sign:
                        pin = questionary.password("Digite o PIN (senha) do seu Token A3:").ask()
                        if pin:
                            use_tsa = questionary.confirm("Deseja incluir Carimbo de Tempo (TSA) para atestar a data/hora exata? (Requer Internet)").ask()
                            tsa_url = None
                            if use_tsa:
                                tsa_choice = questionary.select(
                                    "Escolha o provedor de Carimbo de Tempo (TSA):",
                                    choices=[
                                        "http://timestamp.digicert.com (DigiCert - Internacional)",
                                        "https://freetsa.org/tsr (FreeTSA - Internacional)",
                                        "http://timestamp.sectigo.com (Sectigo - Internacional)",
                                        "URL Personalizada (ACT ICP-Brasil)"
                                    ]
                                ).ask()
                                
                                if tsa_choice == "URL Personalizada (ACT ICP-Brasil)":
                                    tsa_url = questionary.text("Digite a URL do seu provedor TSA pago (ICP-Brasil):").ask()
                                elif tsa_choice:
                                    tsa_url = tsa_choice.split(" ")[0]
                                    
                            tasks = []
                            for p in selected_to_sign:
                                in_path = target_dir / p
                                out_path = ops_dir / f"{in_path.stem}_assinado.pdf"
                                tasks.append((in_path, out_path))
                                
                            from litisdoc.backends.sign import sign_batch_with_a3
                            sign_batch_with_a3(tasks, pin, tsa_url)
                            console.print("[bold green]\nAssinatura em lote finalizada![/bold green]")
                    continue
                
            # Se chegou aqui, é um PDF individual
            selected_pdf_name = selected_item.replace("📄 ", "")
            selected_pdf = target_dir / selected_pdf_name
            
            # Loop do mesmo PDF
            while True:
                op = questionary.select(
                    f"O que deseja fazer com '{selected_pdf_name}'?",
                    choices=[
                        "Informações do PDF",
                        "Comprimir",
                        "Converter para PDF/A (Arquivamento)",
                        "Assinar com Token A3 (ICP-Brasil)",
                        "Verificar Assinaturas",
                        "Linearizar (Fast Web View)",
                        "Preparar para Impressão (Formato Livreto)",
                        "Paginação Sequencial (Bates Stamping)",
                        "Reordenar Páginas",
                        "Comparar com outro PDF (Diff)",
                        "Separar Páginas (Split / Remover)",
                        "Rotacionar",
                        "Aplicar OCR",
                        "Renderizar para Imagens (JPG)",
                        "Extrair Texto",
                        "Extrair Imagens",
                        "Inserir Marca D'água",
                        "Proteger com Senha",
                        "Remover Senha (Desbloquear)",
                        "Limpar Metadados (Anonimizar)",
                        "Remover Histórico Oculto (Scrub)",
                        "<- Voltar para o Menu Principal"
                    ],
                    use_indicator=True
                ).ask()
                
                if op is None or op == "<- Voltar para o Menu Principal":
                    break
                    
                try:
                    if op == "Informações do PDF":
                        get_info(selected_pdf)

                    elif op == "Verificar Assinaturas":
                        verify_signatures(selected_pdf)
                        
                    elif op == "Comprimir":
                        level = questionary.select(
                            "Escolha o nível de compressão:",
                            choices=["screen", "ebook", "printer", "prepress"]
                        ).ask()
                        if level:
                            out = ops_dir / f"{selected_pdf.stem}_comprimido.pdf"
                            compress_pdf(selected_pdf, out, level)
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Extrair Texto":
                        out = ops_dir / f"{selected_pdf.stem}.txt"
                        extract_text(selected_pdf, out, preserve_layout=True)
                        
                    elif op == "Extrair Imagens":
                        out_dir = ops_dir / f"{selected_pdf.stem}_imagens"
                        extract_images(selected_pdf, out_dir)
                        
                    elif op == "Renderizar para Imagens (JPG)":
                        out_dir = ops_dir / f"{selected_pdf.stem}_paginas"
                        render_to_images(selected_pdf, out_dir)
                        
                    elif op == "Separar Páginas (Split / Remover)":
                        pages = questionary.text(
                            "Digite as páginas a extrair (ex: 119-124, 1,3,5) ou deixe vazio para salvar folha por folha:"
                        ).ask()
                        out_dir = ops_dir / f"{selected_pdf.stem}_split"
                        split_pdf(selected_pdf, out_dir, pages=pages if pages else "")
                        
                    elif op == "Rotacionar":
                        angle = questionary.select(
                            "Escolha o ângulo:",
                            choices=["+90", "-90", "+180"]
                        ).ask()
                        if angle:
                            out = ops_dir / f"{selected_pdf.stem}_rotate.pdf"
                            rotate_pdf(selected_pdf, out, angle)
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Aplicar OCR":
                        lang = questionary.text("Idioma do OCR (ex: por, eng):", default="por").ask()
                        if lang:
                            out = ops_dir / f"{selected_pdf.stem}_ocr.pdf"
                            apply_ocr(selected_pdf, out, lang=lang, force=False, deskew=True)
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Inserir Marca D'água":
                        text = questionary.text("Texto da marca d'água:", default="CONFIDENCIAL").ask()
                        if text:
                            out = ops_dir / f"{selected_pdf.stem}_marcado.pdf"
                            add_watermark(selected_pdf, out, text)
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Proteger com Senha":
                        pwd = questionary.password("Digite a senha para proteger:").ask()
                        if pwd:
                            out = ops_dir / f"{selected_pdf.stem}_protegido.pdf"
                            encrypt_pdf(selected_pdf, out, pwd)
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Remover Senha (Desbloquear)":
                        pwd = questionary.password("Digite a senha ATUAL do PDF:").ask()
                        if pwd:
                            out = ops_dir / f"{selected_pdf.stem}_desbloqueado.pdf"
                            decrypt_pdf(selected_pdf, out, pwd)
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Limpar Metadados (Anonimizar)":
                        out = ops_dir / f"{selected_pdf.stem}_limpo.pdf"
                        clear_metadata(selected_pdf, out)
                        selected_pdf = out
                        selected_pdf_name = out.name
                        
                    elif op == "Remover Histórico Oculto (Scrub)":
                        out = ops_dir / f"{selected_pdf.stem}_limpo_scrub.pdf"
                        scrub_pdf(selected_pdf, out)
                        selected_pdf = out
                        selected_pdf_name = out.name
                        
                    elif op == "Converter para PDF/A (Arquivamento)":
                        out = ops_dir / f"{selected_pdf.stem}_pdfa.pdf"
                        convert_to_pdfa(selected_pdf, out)
                        selected_pdf = out
                        selected_pdf_name = out.name
                        
                    elif op == "Linearizar (Fast Web View)":
                        out = ops_dir / f"{selected_pdf.stem}_linearizado.pdf"
                        linearize_pdf(selected_pdf, out)
                        selected_pdf = out
                        selected_pdf_name = out.name
                        
                    elif op == "Paginação Sequencial (Bates Stamping)":
                        prefix = questionary.text("Prefixo (ex: Fl. ):", default="Fl. ").ask()
                        start_num_str = questionary.text("Número inicial da página:", default="1").ask()
                        if start_num_str and start_num_str.isdigit():
                            out = ops_dir / f"{selected_pdf.stem}_paginado.pdf"
                            add_pagination(selected_pdf, out, prefix=prefix, start_num=int(start_num_str))
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Preparar para Impressão (Formato Livreto)":
                        out = ops_dir / f"{selected_pdf.stem}_livreto.pdf"
                        create_booklet(selected_pdf, out)
                        selected_pdf = out
                        selected_pdf_name = out.name
                            
                    elif op == "Assinar com Token A3 (ICP-Brasil)":
                        pin = questionary.password("Digite o PIN (senha) do seu Token A3:").ask()
                        if pin:
                            use_tsa = questionary.confirm("Deseja incluir Carimbo de Tempo (TSA)? (Requer Internet)").ask()
                            tsa_url = None
                            if use_tsa:
                                tsa_choice = questionary.select(
                                    "Escolha o provedor de Carimbo de Tempo (TSA):",
                                    choices=[
                                        "http://timestamp.digicert.com (DigiCert - Internacional)",
                                        "https://freetsa.org/tsr (FreeTSA - Internacional)",
                                        "http://timestamp.sectigo.com (Sectigo - Internacional)",
                                        "URL Personalizada (ACT ICP-Brasil)"
                                    ]
                                ).ask()
                                
                                if tsa_choice == "URL Personalizada (ACT ICP-Brasil)":
                                    tsa_url = questionary.text("Digite a URL do seu provedor TSA pago (ICP-Brasil):").ask()
                                elif tsa_choice:
                                    tsa_url = tsa_choice.split(" ")[0]
                                    
                            out = ops_dir / f"{selected_pdf.stem}_assinado.pdf"
                            sign_with_a3(selected_pdf, out, pin, tsa_url)
                            selected_pdf = out
                            selected_pdf_name = out.name
                            
                    elif op == "Reordenar Páginas":
                        pages = questionary.text(
                            "Digite a nova ordem das páginas (ex: 3,2,1 ou 1-5,10,6-9):"
                        ).ask()
                        if pages:
                            out = ops_dir / f"{selected_pdf.stem}_reordenado.pdf"
                            split_pdf(selected_pdf, ops_dir, pages=pages)
                            # O output do qpdf será out_dir/nome_extraido.pdf, vamos mover
                            temp_out = ops_dir / f"{selected_pdf.stem}_extraido.pdf"
                            if temp_out.exists():
                                temp_out.rename(out)
                                console.print(f"[bold green]Reordenado e salvo em {out.name}[/bold green]")
                                selected_pdf = out
                                selected_pdf_name = out.name
                                
                    elif op == "Comparar com outro PDF (Diff)":
                        # Lista outros PDFs da pasta para escolher
                        other_pdfs = [p.name for p in pdfs if p.name != selected_pdf_name]
                        if not other_pdfs:
                            console.print("[yellow]Não há outros PDFs nesta pasta para comparar.[/yellow]")
                        else:
                            pdf2_name = questionary.select(
                                f"Comparar '{selected_pdf_name}' com qual PDF?",
                                choices=other_pdfs
                            ).ask()
                            if pdf2_name:
                                pdf2 = target_dir / pdf2_name
                                out = ops_dir / f"{selected_pdf.stem}_vs_{Path(pdf2_name).stem}_diff.pdf"
                                compare_pdfs(selected_pdf, pdf2, out)
                            
                except Exception as e:
                    console.print(f"[bold red]Erro ao executar a operação:[/bold red] {e}")
                
                continuar = questionary.confirm(
                    f"Deseja realizar mais alguma operação em '{selected_pdf_name}'?"
                ).ask()
                
                if not continuar:
                    break

            if single_file_mode:
                # If they were in single file mode, going back means returning to prompt for another path
                break

if __name__ == "__main__":
    run_tui()
