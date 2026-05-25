"""Utilidades de interfaz de usuario: formateo, prompts y validaciones."""
import csv
import re

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich import box

console = Console()


def limpiar():
    console.clear()


def encabezado(titulo, subtitulo=""):
    console.print()
    texto = Text(justify="center")
    texto.append(titulo, style="bold cyan")
    if subtitulo:
        texto.append(f"\n{subtitulo}", style="dim white")
    console.print(Panel(
        Align.center(texto),
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        padding=(0, 4),
    ))


def ok(msg):
    console.print(f"\n[bold green]  ✔  {msg}[/]")


def err(msg):
    console.print(f"\n[bold red]  ✖  {msg}[/]")


def warn(msg):
    console.print(f"\n[bold yellow]  ⚠  {msg}[/]")


def info(msg):
    console.print(f"\n[bold cyan]  ℹ  {msg}[/]")


def pausar():
    console.print()
    Prompt.ask("[dim]  Presione Enter para continuar[/]", default="")


def mostrar_menu(titulo, opciones):
    texto = Text()
    for i, op in enumerate(opciones, 1):
        texto.append(f"  [{i}]  ", style="bold cyan")
        texto.append(f"{op}\n", style="white")
    console.print()
    console.print(Panel(
        texto,
        title=f"[bold cyan]{titulo}[/]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 1),
    ))
    return Prompt.ask("[cyan]  Opción[/]").strip()


def pedir_int(prompt):
    val = Prompt.ask(f"[white]  {prompt}[/]").strip()
    try:
        return int(val)
    except ValueError:
        err("Valor numérico inválido.")
        return None


def pedir_float(prompt, default=0.0):
    val = Prompt.ask(f"[white]  {prompt}[/]", default=str(default)).strip()
    try:
        return float(val)
    except ValueError:
        err("Valor decimal inválido.")
        return default


def pedir_fecha(prompt):
    while True:
        val = Prompt.ask(f"[white]  {prompt} [dim](YYYY-MM-DD)[/][/]").strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
            return val
        err("Formato inválido. Use YYYY-MM-DD  (ej: 2025-06-15)")


def pedir_email(prompt, requerido=True, default=""):
    while True:
        val = Prompt.ask(f"[white]  {prompt}[/]", default=default).strip()
        if not val:
            if not requerido:
                return val
            err("El email es obligatorio.")
            continue
        if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", val):
            return val
        err("Formato de email inválido. Ej: usuario@dominio.com")


def pedir_telefono(prompt, requerido=False, default=""):
    while True:
        val = Prompt.ask(f"[white]  {prompt}[/]", default=default).strip()
        if not val:
            if not requerido:
                return val
            err("El teléfono es obligatorio.")
            continue
        if re.match(r"^\d+$", val):
            return val
        err("El teléfono debe contener solo números, sin espacios ni guiones.")


def exportar_csv(datos, nombre_archivo):
    if not datos:
        warn("No hay datos para exportar.")
        return
    try:
        with open(nombre_archivo, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=datos[0].keys())
            writer.writeheader()
            writer.writerows(datos)
        ok(f"Exportado a [bold]{nombre_archivo}[/]")
    except Exception as e:
        err(f"Error al exportar: {e}")
