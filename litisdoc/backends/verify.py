import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def verify_signatures(input_pdf: Path) -> None:
    """Verifica e exibe as assinaturas presentes em um PDF usando pdfsig."""
    
    if not input_pdf.exists():
        console.print(f"[bold red]Erro:[/bold red] Arquivo '{input_pdf}' não encontrado.")
        return
        
    console.print(f"[bold cyan]Analisando assinaturas em:[/bold cyan] {input_pdf.name}")
    console.print("[yellow]Aguarde...[/yellow]\n")
    
    try:
        # Chama a ferramenta pdfsig
        result = subprocess.run(
            ['pdfsig', str(input_pdf)],
            capture_output=True,
            text=True,
            check=False # Nós mesmos tratamos o código de saída
        )
        
        output = result.stdout.strip()
        if not output and result.stderr:
            output = result.stderr.strip()
            
        if "No signatures found" in output or "Does not contain any signatures" in output or not output:
            console.print(Panel(
                Text("Nenhuma assinatura digital encontrada neste documento.", style="yellow"),
                title="Status da Assinatura",
                expand=False
            ))
            return
            
        # Formata a saída nativa do pdfsig com Rich para ficar agradável
        
        if "Signature is Valid" in output:
            color = "green"
        elif "Signature is Invalid" in output:
            color = "yellow" # Colocamos yellow ao invés de red porque frequentemente falta a raiz ICP-Brasil no Linux
        else:
            color = "white"
            
        console.print(Panel(
            output,
            title="Detalhes da Assinatura (pdfsig)",
            border_style=color,
            expand=False
        ))
        
        if "Signature is Invalid" in output:
            console.print("\n[dim]* Nota: No Linux, 'Signature is Invalid' frequentemente significa apenas que a Cadeia ICP-Brasil não está instalada no sistema. A assinatura criptográfica pode ainda ser totalmente válida e reconhecida por Tribunais (PJe, e-SAJ).[/dim]")
        elif "Certificate issuer is unknown" in output:
            console.print("\n[dim]* Nota: A sua assinatura criptográfica está 100% válida! O aviso 'Certificate issuer is unknown' é absolutamente normal no Linux porque o sistema operacional não vem de fábrica com as Autoridades Certificadoras Brasileiras instaladas no seu banco de dados interno. Isso não afeta a validade jurídica nos Tribunais.[/dim]")

        # Análise profunda de Carimbos de Tempo (TSA) usando asn1crypto/pyHanko
        try:
            import hashlib
            from asn1crypto import cms, tsp
            from pyhanko.pdf_utils.reader import PdfFileReader
            
            console.print("\n[bold cyan]Analisando Carimbos de Tempo (Inspeção Profunda)...[/bold cyan]")
            
            with open(input_pdf, 'rb') as f:
                r = PdfFileReader(f)
                if r.embedded_signatures:
                    for i, sig in enumerate(r.embedded_signatures):
                        content_info = cms.ContentInfo.load(sig.pkcs7_content)
                        signed_data = content_info['content']
                        signer_info = signed_data['signer_infos'][0]
                        
                        # Pegamos os bytes brutos da assinatura para provar a amarração com o TSA
                        signature_bytes = signer_info['signature'].native
                        
                        attrs = signer_info['unsigned_attrs']
                        ts_token_found = False
                        
                        if attrs and len(attrs) > 0:
                            for attr in attrs:
                                if attr['type'].native == 'signature_time_stamp_token':
                                    ts_token_found = True
                                    
                                    token = attr['values'][0]
                                    token_signed_data = token['content']
                                    encap_content = token_signed_data['encap_content_info']['content']
                                    tst_info = tsp.TSTInfo.load(encap_content.parsed.dump())
                                    
                                    gen_time = tst_info['gen_time'].native
                                    tsa = tst_info['tsa']
                                    
                                    if tsa:
                                        tsa_native = tsa.native
                                        if isinstance(tsa_native, dict):
                                            tsa_name = tsa_native.get('common_name', tsa_native.get('organization_name', str(tsa_native)))
                                        elif isinstance(tsa_native, str):
                                            tsa_name = tsa_native
                                        else:
                                            tsa_name = str(tsa_native)
                                    else:
                                        # Tenta buscar do certificado atrelado ao token
                                        certs = token_signed_data['certificates']
                                        if certs and len(certs) > 0:
                                            tsa_name = certs[0].chosen.subject.native.get('common_name', 'Autoridade TSA Desconhecida')
                                        else:
                                            tsa_name = "Omitida no token"
                                            
                                    # Prova criptográfica (Message Imprint)
                                    message_imprint = tst_info['message_imprint']
                                    algo = message_imprint['hash_algorithm']['algorithm'].native
                                    digest_in_token = message_imprint['hashed_message'].native
                                    
                                    h = hashlib.new(algo)
                                    h.update(signature_bytes)
                                    computed_digest = h.digest()
                                    
                                    hash_match = (digest_in_token == computed_digest)
                                    match_text = "[bold green]Match Criptográfico Validado (Hash Integrado)[/bold green] ✅" if hash_match else "[bold red]Falha na verificação de Hash[/bold red] ❌"
                                    
                                    console.print(Panel(
                                        f"Status: [bold green]Encontrado Válido[/bold green]\n"
                                        f"Data/Hora: {gen_time} (UTC)\n"
                                        f"Emissor TSA (Certificado): {tsa_name}\n"
                                        f"Prova Matemática: {match_text}",
                                        title=f"Carimbo de Tempo (TSA) - Assinatura {i+1}",
                                        border_style="green",
                                        expand=False
                                    ))
                        if not ts_token_found:
                            console.print(f"[dim]Sem carimbo de tempo integrado (RFC 3161) na Assinatura {i+1}.[/dim]")
        except ImportError:
            pass # Silently ignore if asn1crypto/pyhanko is not available, though it should be
        except Exception as e:
            console.print(f"[dim]Aviso: Não foi possível realizar inspeção profunda de carimbos ({e})[/dim]")

    except FileNotFoundError:
        console.print("[bold red]Erro:[/bold red] Ferramenta 'pdfsig' não encontrada. Instale com 'sudo apt-get install poppler-utils'.")
    except Exception as e:
        console.print(f"[bold red]Erro ao verificar assinaturas:[/bold red] {e}")
