import subprocess
import sys
from pathlib import Path
from litisdoc.core.deps import check_dependency
from rich.console import Console

console = Console()

def search_in_pdfs(target_dir: Path, query: str, use_regex: bool = False) -> None:
    """Busca um texto em todos os PDFs de um diretório usando pdfgrep."""
    check_dependency("pdfgrep", "pdfgrep")
    
    # -F para string fixa (Busca simples), -P para Perl-Regex (Busca Avançada)
    regex_flag = "-P" if use_regex else "-F"
    cmd = f'pdfgrep -r -i -n {regex_flag} --color=always "{query}" "{target_dir}"'
    
    console.print(f"[bold cyan]🔍 Buscando por '{query}' em '{target_dir.name}'...[/bold cyan]\n")
    try:
        # Popen para printar ao vivo com as cores nativas do pdfgrep no TTY
        process = subprocess.run(
            cmd, 
            shell=True,
        )
        if process.returncode == 0:
            console.print("\n[bold green]Busca finalizada.[/bold green]")
        elif process.returncode == 1:
            console.print(f"\n[yellow]Nenhum resultado encontrado para '{query}'.[/yellow]")
        else:
            console.print("\n[bold red]Erro ao executar a busca.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Exceção ao buscar:[/bold red] {e}")
