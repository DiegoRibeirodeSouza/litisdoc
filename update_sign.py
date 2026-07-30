import re

with open("litisdoc/backends/sign.py", "r") as f:
    content = f.read()

# 1. Add the new stamp helper functions before sign_batch_with_a3
helpers = """
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

def sign_batch_with_a3
"""
content = content.replace("def sign_batch_with_a3", helpers.strip())

# 2. Modify the style logic in sign_batch_with_a3
old_logic = """            is_diego = "DIEGO RIBEIRO DE SOUZA" in cert_name.upper()
            stamp_pdf_path = None
            
            if is_diego:
                # Gerar o carimbo dinâmico gráfico apenas para o autor do app
                stamp_pdf_path = _create_dynamic_stamp(cert_name)
                stamp_style = StaticStampStyle.from_pdf_file(stamp_pdf_path, border_width=0)
            else:
                # Carimbo genérico textual em fallback para o público geral
                stamp_text = f"[ ICP-Brasil ] Documento assinado eletronicamente por {cert_name} em %(ts)s."
                stamp_style = TextStampStyle(
                    stamp_text=stamp_text,
                    border_width=0,
                    background_opacity=0,
                )"""

new_logic = """            is_diego = "DIEGO RIBEIRO DE SOUZA" in cert_name.upper()
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
"""
content = content.replace(old_logic, new_logic)

# 3. Modify the new_field_spec creation logic in the loop
old_box = """                        if is_diego:
                            sig_box = (97, 20, 497, 220)
                        else:
                            sig_box = (10, 75, 585, 95)
                            
                        new_field_spec = SigFieldSpec(
                            sig_field_name='Signature1',
                            on_page=-1, # última página
                            box=sig_box
                        )"""
                        
new_box = """                        if "Completa" in chosen_style:
                            sig_box = (97, 20, 497, 220)
                            new_field_spec = SigFieldSpec(sig_field_name='Signature1', on_page=-1, box=sig_box)
                        elif "Vertical" in chosen_style:
                            sig_box = (570, 50, 595, 650) # margem direita
                            new_field_spec = SigFieldSpec(sig_field_name='Signature1', on_page=-1, box=sig_box)
                        elif "CMU" in chosen_style:
                            sig_box = (72, 20, 522, 70) # centralizado inferior
                            new_field_spec = SigFieldSpec(sig_field_name='Signature1', on_page=-1, box=sig_box)
                        elif "Padrão" in chosen_style:
                            sig_box = (10, 75, 585, 95)
                            new_field_spec = SigFieldSpec(sig_field_name='Signature1', on_page=-1, box=sig_box)
                        else:
                            # Oculta
                            new_field_spec = SigFieldSpec(sig_field_name='Signature1', on_page=-1, box=(0,0,0,0))
"""
content = content.replace(old_box, new_box)

with open("litisdoc/backends/sign.py", "w") as f:
    f.write(content)
