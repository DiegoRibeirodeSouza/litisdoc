import os
import uuid
from pathlib import Path
from rich.console import Console
import tempfile
import datetime
import os
import uuid
import questionary
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

console = Console()

def _create_dynamic_stamp(signer_name: str) -> str:
    """Gera um PDF temporário contendo o carimbo visual (Estilo A) e retorna o caminho do arquivo."""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    
    # Tamanho mais compacto para caber em PDFs com margens curtas (ex: páginas de 453pt)
    box_width = 400
    box_height = 200
    c = canvas.Canvas(tmp_file.name, pagesize=(box_width, box_height))
    
    # Centralizado na nova caixa
    x_center = box_width / 2
    
    # Resolver caminhos absolutos dos assets
    assets_dir = os.path.expanduser("~/.config/litisdoc/assets")
    font_reg = os.path.join(assets_dir, "cmunrm.ttf")
    font_bold = os.path.join(assets_dir, "cmunbx.ttf")
    img_path = os.path.join(assets_dir, "assinatura_limpa.png")
    
    # Registrar fontes, falhando silenciosamente se não existirem (fallback interno do ReportLab ocorrerá ou erro)
    if os.path.exists(font_reg) and os.path.exists(font_bold):
        pdfmetrics.registerFont(TTFont('CMU-Reg', font_reg))
        pdfmetrics.registerFont(TTFont('CMU-Bold', font_bold))
        f_reg, f_bold = "CMU-Reg", "CMU-Bold"
    else:
        f_reg, f_bold = "Helvetica", "Helvetica-Bold"

    base_y = 30 # Y relativo ao crop box que definiremos
    
    # 1. Rubrica
    if os.path.exists(img_path):
        img = Image.open(img_path)
        img_w, img_h = img.size
        aspect = img_h / float(img_w)
        target_w = 153  # Aumentado em 70% (antes 90)
        target_h = target_w * aspect
        c.drawImage(img_path, x_center - target_w/2, base_y + 10, width=target_w, height=target_h, mask='auto')
    
    # 2. Linha mais compacta
    c.setLineWidth(0.5)
    c.line(x_center - 130, base_y + 10, x_center + 130, base_y + 10)
    
    # 3. Textos
    data_str = f"Assinado eletronicamente em {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    # Formatação do nome extraindo OAB se possível
    nome_str = signer_name.upper()
    if "DIEGO RIBEIRO DE SOUZA" in nome_str:
        nome_str = "Diego Ribeiro de Souza - OAB/MG 211.002"
        
    c.setFont(f_bold, 11)
    c.drawCentredString(x_center, base_y - 3, nome_str)
    c.setFont(f_reg, 10)
    c.drawCentredString(x_center, base_y - 15, data_str)
    
    c.showPage()
    c.save()
    return tmp_file.name


def _create_vertical_stamp(signer_name: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    box_width = 30
    box_height = 600
    c = canvas.Canvas(tmp_file.name, pagesize=(box_width, box_height))
    c.translate(10, 20)
    c.rotate(90)
    data_str = f"Documento assinado eletronicamente por {signer_name} em {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    c.setFont("Helvetica", 10)
    c.drawString(0, 0, data_str)
    c.showPage()
    c.save()
    return tmp_file.name

def _create_cmu_stamp(signer_name: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    box_width = 450
    box_height = 50
    c = canvas.Canvas(tmp_file.name, pagesize=(box_width, box_height))
    assets_dir = os.path.expanduser("~/.config/litisdoc/assets")
    font_reg = os.path.join(assets_dir, "cmunrm.ttf")
    if os.path.exists(font_reg):
        pdfmetrics.registerFont(TTFont('CMU-Reg', font_reg))
        f_reg = "CMU-Reg"
    else:
        f_reg = "Helvetica"
        
    data_str = f"Assinado digitalmente por {signer_name} em {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    c.setFont(f_reg, 12)
    c.drawCentredString(box_width / 2, 20, data_str)
    c.showPage()
    c.save()
    return tmp_file.name

def sign_batch_with_a3(tasks: list, pin: str) -> None:
    """Assina um ou múltiplos PDFs em lote usando Token A3 (PKCS#11) via pyHanko, reutilizando a sessão."""
    try:
        from pyhanko.sign import signers
        from pyhanko.sign.pkcs11 import PKCS11Signer
        from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    except ImportError:
        console.print("[bold red]Erro:[/bold red] O pacote pyhanko[pkcs11] não está instalado ou configurado.")
        return

    # Buscar biblioteca PKCS#11 do sistema (OpenSC é o mais comum no Linux)
    pkcs11_paths = [
        "/usr/lib/safesign-private/libaetpkss.so.3",
        "/usr/lib/safesign-private/libaetpkss.so",
        "/usr/lib/x86_64-linux-gnu/opensc-pkcs11.so",
        "/usr/lib/opensc-pkcs11.so",
        "/usr/lib/libeToken.so",
        "/usr/lib/libaetpkss.so.3",
        "/usr/local/lib/libeToken.so",
        "/usr/lib/libwdkP11.so", # Certisign
        "/usr/lib/watchdata/ICP/lib/libwdkP11.so", # WatchData
        "/usr/lib/libbit4xpki.so" # Bit4id
    ]
    
    try:
        import pkcs11
        
        module_path = None
        token = None
        
        for p in pkcs11_paths:
            if os.path.exists(p):
                try:
                    lib = pkcs11.lib(p)
                    tokens = list(lib.get_tokens())
                    if tokens:
                        module_path = p
                        token = tokens[0]
                        break
                except Exception:
                    continue
        
        if not module_path or not token:
            console.print("[bold red]Erro:[/bold red] Nenhum token/smartcard detectado nas bibliotecas padrões. Conecte o dispositivo A3 e tente novamente.")
            return
            
        console.print(f"[bold green]Módulo PKCS#11 detectado:[/bold green] {module_path}")
        console.print(f"[bold green]Token encontrado:[/bold green] {token.label}")
        console.print("[yellow]Comunicando com o Token A3 (abrindo sessão criptográfica única)...[/yellow]")
        
        with token.open(user_pin=pin) as session:
            # Lista certificados disponíveis no token
            certs = list(session.get_objects({pkcs11.Attribute.CLASS: pkcs11.ObjectClass.CERTIFICATE}))
            cert_options = []
            for c in certs:
                try:
                    label = c[pkcs11.Attribute.LABEL]
                    if isinstance(label, bytes):
                        label = label.decode('utf-8', errors='ignore')
                    cid = c[pkcs11.Attribute.ID]
                    if label and cid:
                        cert_options.append({'label': label, 'id': cid})
                except Exception:
                    pass
            
            chosen_cert_id = None
            
            for c in cert_options:
                if c['label'] == "DIEGO RIBEIRO DE SOUZA 2024-10-09 20:22:25":
                    chosen_cert_id = c['id']
                    chosen_label = c['label']
                    break
            
            if not chosen_cert_id:
                if len(cert_options) > 1:
                    choices = [c['label'] for c in cert_options]
                    chosen_label = questionary.select(
                        "Foram encontrados múltiplos certificados no Token. Selecione qual deseja utilizar:",
                        choices=choices
                    ).ask()
                    
                    if not chosen_label:
                        console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
                        return
                    
                    for c in cert_options:
                        if c['label'] == chosen_label:
                            chosen_cert_id = c['id']
                            break
                elif len(cert_options) == 1:
                    chosen_cert_id = cert_options[0]['id']
                    chosen_label = cert_options[0]['label']
                
            from pyhanko.sign.signers.pdf_signer import PdfSigner
            from pyhanko.sign.fields import SigFieldSpec
            from pyhanko.stamp import StaticStampStyle, TextStampStyle
            import io
            
            cert_name = "Certificado ICP-Brasil"
            if chosen_cert_id:
                for c in cert_options:
                    if c['id'] == chosen_cert_id:
                        cert_name = c['label'].split(' emitido ')[0].split(' (')[0].split(' 20')[0].strip()
                        break
                        
            is_diego = "DIEGO RIBEIRO DE SOUZA" in cert_name.upper()
            stamp_pdf_path = None
            
            style_options = [
                "Oculta (apenas criptografia, sem marca visual)",
                "Texto Vertical (lateral direita, de baixo para cima)",
                "Texto CMU (fonte clássica, tamanho 12)",
                "Texto Padrão"
            ]
            
            if is_diego:
                style_options.append("Visual Completa (Brasão + Rubrica)")
                
            chosen_style = questionary.select(
                "Escolha o estilo da assinatura visual no PDF:",
                choices=style_options
            ).ask()
            
            if not chosen_style:
                console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
                return
                
            stamp_style = None
            if "Completa" in chosen_style:
                stamp_pdf_path = _create_dynamic_stamp(cert_name)
                stamp_style = StaticStampStyle.from_pdf_file(stamp_pdf_path, border_width=0)
            elif "Vertical" in chosen_style:
                stamp_pdf_path = _create_vertical_stamp(cert_name)
                stamp_style = StaticStampStyle.from_pdf_file(stamp_pdf_path, border_width=0)
            elif "CMU" in chosen_style:
                stamp_pdf_path = _create_cmu_stamp(cert_name)
                stamp_style = StaticStampStyle.from_pdf_file(stamp_pdf_path, border_width=0)
            elif "Padrão" in chosen_style:
                stamp_text = f"[ ICP-Brasil ] Documento assinado eletronicamente por {cert_name} em %(ts)s."
                stamp_style = TextStampStyle(stamp_text=stamp_text, border_width=0, background_opacity=0)
            # Se for "Oculta", stamp_style = None


            for input_pdf, output_pdf in tasks:
                try:
                    dynamic_sig_name = f'Signature_{uuid.uuid4().hex[:8]}'
                    # Instanciar o signer e meta a cada arquivo para evitar 'stale state' no driver PKCS11
                    signer_kwargs = {'pkcs11_session': session, 'use_raw_mechanism': True}
                    if chosen_cert_id:
                        signer_kwargs['cert_id'] = chosen_cert_id
                    signer = PKCS11Signer(**signer_kwargs)

                    meta = signers.PdfSignatureMetadata(
                        field_name=dynamic_sig_name,
                        reason='Assinado digitalmente via LitisDoc',
                    )

                    with open(input_pdf, 'rb') as doc_in:
                        w = IncrementalPdfFileWriter(doc_in)
                        
                        if "Completa" in chosen_style:
                            sig_box = (97, 20, 497, 220)
                            new_field_spec = SigFieldSpec(sig_field_name=dynamic_sig_name, on_page=-1, box=sig_box)
                        elif "Vertical" in chosen_style:
                            sig_box = (570, 50, 595, 650) # margem direita
                            new_field_spec = SigFieldSpec(sig_field_name=dynamic_sig_name, on_page=-1, box=sig_box)
                        elif "CMU" in chosen_style:
                            sig_box = (72, 20, 522, 70) # centralizado inferior
                            new_field_spec = SigFieldSpec(sig_field_name=dynamic_sig_name, on_page=-1, box=sig_box)
                        elif "Padrão" in chosen_style:
                            sig_box = (10, 75, 585, 95)
                            new_field_spec = SigFieldSpec(sig_field_name=dynamic_sig_name, on_page=-1, box=sig_box)
                        else:
                            # Oculta
                            new_field_spec = SigFieldSpec(sig_field_name=dynamic_sig_name, on_page=-1, box=(0,0,0,0))

                        
                        pdf_signer = PdfSigner(
                            signature_meta=meta,
                            signer=signer,
                            stamp_style=stamp_style,
                            new_field_spec=new_field_spec
                        )
                        
                        # Usar um buffer em memória para prevenir corrompimento caso o token falhe no meio da operação
                        out_buffer = io.BytesIO()
                        pdf_signer.sign_pdf(
                            w, existing_fields_only=False, output=out_buffer
                        )
                        
                        # Se não houve erro, salvar no arquivo final
                        with open(output_pdf, 'wb') as doc_out:
                            doc_out.write(out_buffer.getvalue())
                            
                    console.print(f"[bold green]Sucesso:[/bold green] Arquivo assinado e salvo em {output_pdf.name}")
                except Exception as ex:
                    console.print(f"[bold red]Falha ao assinar '{input_pdf.name}':[/bold red] {ex}")
            
            # Limpar PDF temporário se gerado
            try:
                if stamp_pdf_path and os.path.exists(stamp_pdf_path):
                    os.remove(stamp_pdf_path)
            except Exception:
                pass

                    
    except Exception as e:
        console.print(f"[bold red]Falha na comunicação com o Token:[/bold red] {e}")
        console.print("Verifique se o token A3 está bem conectado e se a senha está correta.")

def sign_with_a3(input_pdf: Path, output_pdf: Path, pin: str) -> None:
    sign_batch_with_a3([(input_pdf, output_pdf)], pin)
