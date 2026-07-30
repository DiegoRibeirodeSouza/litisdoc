import os
import tempfile
import textwrap
import datetime
import uuid
from pathlib import Path
from typing import List
from rich.console import Console
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz  # PyMuPDF

console = Console()

A4_WIDTH, A4_HEIGHT = A4
MARGIN = 50

def _create_cover_page(title: str, ref_hash: str) -> str:
    """Gera uma página de rosto em PDF com título e Hash de referência."""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp_file.name, pagesize=A4)
    
    # Tenta usar a fonte Computer Modern do cofre
    assets_dir = os.path.expanduser("~/.config/litisdoc/assets")
    font_bold = os.path.join(assets_dir, "cmunbx.ttf")
    font_reg = os.path.join(assets_dir, "cmunrm.ttf")
    
    if os.path.exists(font_bold) and os.path.exists(font_reg):
        pdfmetrics.registerFont(TTFont('CMU-Bold', font_bold))
        pdfmetrics.registerFont(TTFont('CMU-Reg', font_reg))
        f_title = "CMU-Bold"
        f_sub = "CMU-Reg"
    else:
        f_title = "Helvetica-Bold"
        f_sub = "Helvetica"
        
    # Fundo branco e estética minimalista
    c.setFillColorRGB(0, 0, 0)
    
    # Título principal centralizado no meio da página
    c.setFont(f_title, 28)
    y_center = A4_HEIGHT / 2
    lines = textwrap.wrap(title.upper(), width=35)
    y_pos = y_center + 40 + (len(lines) - 1) * 35
    for line in lines:
        c.drawCentredString(A4_WIDTH / 2, y_pos, line)
        y_pos -= 35
    
    # Linha elegante
    c.setLineWidth(1)
    c.line(A4_WIDTH / 2 - 200, y_center + 15, A4_WIDTH / 2 + 200, y_center + 15)
    
    # Data de geração e Hash de Referência
    c.setFont(f_sub, 12)
    data_str = f"Gerado em {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    c.drawCentredString(A4_WIDTH / 2, y_center - 20, data_str)
    
    c.setFont(f_title, 14)
    c.drawCentredString(A4_WIDTH / 2, y_center - 50, f"Ref*: {ref_hash}")
    
    # Aviso para o Tribunal
    c.setFont(f_sub, 9)
    notice = "* Código Hash de controle privativo gerado pelo software LitisDoc. Não se confunde com o ID de protocolo do Tribunal."
    c.drawCentredString(A4_WIDTH / 2, y_center - 80, notice)
    
    c.showPage()
    c.save()
    return tmp_file.name

def _fit_rect(src_w: float, src_h: float, max_w: float, max_h: float) -> fitz.Rect:
    """Calcula o retângulo centralizado escalonado mantendo a proporção."""
    aspect = src_h / src_w
    if src_w > max_w or src_h > max_h:
        # Se for maior, escala para baixo
        if (max_w * aspect) <= max_h:
            new_w = max_w
            new_h = max_w * aspect
        else:
            new_h = max_h
            new_w = max_h / aspect
    else:
        # Se a imagem for muito pequena, podemos escalá-la para ocupar pelo menos boa parte da folha
        # ou deixá-la no tamanho original (melhor evitar pixelização, deixamos original)
        new_w = src_w
        new_h = src_h
        
    x0 = (A4_WIDTH - new_w) / 2
    y0 = (A4_HEIGHT - new_h) / 2
    return fitz.Rect(x0, y0, x0 + new_w, y0 + new_h)

def create_dossier(title: str, input_paths: List[Path], output_pdf: Path) -> None:
    """Processa todos os inputs, padroniza em A4 e gera o dossiê final."""
    try:
        # Gera o Hash de 15 caracteres (ex: 8F2A3B9C4E1D7X0)
        ref_hash = uuid.uuid4().hex[:15].upper()
        
        # Anexa o hash ao nome do arquivo final (antes da extensão)
        final_output = output_pdf.parent / f"{output_pdf.stem}_{ref_hash}{output_pdf.suffix}"
        
        final_doc = fitz.open()
        
        # 1. Inserir a Capa
        cover_path = _create_cover_page(title, ref_hash)
        cover_doc = fitz.open(cover_path)
        final_doc.insert_pdf(cover_doc)
        cover_doc.close()
        os.remove(cover_path)
        
        # 2. Processar cada arquivo
        usable_w = A4_WIDTH - (2 * MARGIN)
        usable_h = A4_HEIGHT - (2 * MARGIN)
        
        for file_path in input_paths:
            if not file_path.exists():
                console.print(f"[bold yellow]Aviso:[/bold yellow] Arquivo não encontrado: {file_path}")
                continue
                
            ext = file_path.suffix.lower()
            
            if ext in ['.pdf']:
                src_doc = fitz.open(file_path)
                for page_num in range(len(src_doc)):
                    src_page = src_doc[page_num]
                    src_rect = src_page.rect
                    
                    # Cria nova página A4 em branco no documento final
                    new_page = final_doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
                    
                    # Calcula o box para colar a página
                    target_rect = _fit_rect(src_rect.width, src_rect.height, usable_w, usable_h)
                    
                    # Desenha a página do PDF original na nossa folha A4 limpa
                    new_page.show_pdf_page(target_rect, src_doc, page_num)
                    
                    # Título no cabeçalho (Esquerda) e Hash (Direita)
                    new_page.insert_text(fitz.Point(MARGIN, 30), title.upper(), fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
                    
                    # Calcula o alinhamento da hash na direita
                    hash_text = f"Ref*: {ref_hash}"
                    text_length = 95  # Estimativa segura para 15 caracteres size 10
                    new_page.insert_text(fitz.Point(A4_WIDTH - MARGIN - text_length, 30), hash_text, fontname="helv", fontsize=10, color=(0.6, 0.6, 0.6))
                src_doc.close()
                
            elif ext in ['.png', '.jpg', '.jpeg']:
                # É uma imagem
                img_doc = fitz.open(file_path)
                src_rect = img_doc[0].rect
                
                new_page = final_doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
                target_rect = _fit_rect(src_rect.width, src_rect.height, usable_w, usable_h)
                
                # Inserimos os bytes da imagem
                new_page.insert_image(target_rect, filename=str(file_path))
                
                # Título no cabeçalho e Hash na Direita
                new_page.insert_text(fitz.Point(MARGIN, 30), title.upper(), fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
                hash_text = f"Ref*: {ref_hash}"
                text_length = 95  # Estimativa segura
                new_page.insert_text(fitz.Point(A4_WIDTH - MARGIN - text_length, 30), hash_text, fontname="helv", fontsize=10, color=(0.6, 0.6, 0.6))
                img_doc.close()
                
            else:
                console.print(f"[bold yellow]Formato ignorado:[/bold yellow] {file_path}")
                
        # 3. Paginação (Ignorando a capa)
        total_pages = len(final_doc)
        total_content_pages = total_pages - 1
        for i in range(1, total_pages):
            page = final_doc[i]
            page_text = f"Página {i} de {total_content_pages}"
            
            # Centralizado no rodapé
            text_len = 70 # Estimativa de largura para centralizar
            page.insert_text(fitz.Point((A4_WIDTH / 2) - (text_len / 2), A4_HEIGHT - 30), 
                             page_text, fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
                
        # 4. Salvar o documento final
        final_doc.save(final_output)
        final_doc.close()
        
        console.print(f"\n[bold green]✓ Dossiê '{title}' gerado com sucesso! (Ref*: {ref_hash})[/bold green]")
        console.print(f"Salvo em: {final_output.absolute()}\n")
        
    except Exception as e:
        console.print(f"[bold red]Erro crítico ao gerar dossiê:[/bold red] {e}")
