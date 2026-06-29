#!/usr/bin/env python3
"""
Agent OS — CLI / Server Launcher

Usage:
  python run.py                         # interactive single-prompt mode
  python run.py -t "your task here"    # run one task and exit
  python run.py -i                      # interactive loop (multi-task)
  python run.py --api                   # start FastAPI server
"""
import sys
import argparse


def run_cli(task: str | None = None) -> None:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from app.agent.core import agent

    console = Console()
    console.print(
        Panel.fit("[bold blue]🤖 Agent OS[/bold blue]\n[dim]Autonomous General-Purpose Agent[/dim]", border_style="blue")
    )

    if not task:
        console.print("[yellow]Enter your task:[/yellow]")
        try:
            task = input(">> ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Bye.[/red]")
            sys.exit(0)

    if not task:
        console.print("[red]No task provided.[/red]")
        sys.exit(1)

    console.print(f"\n[bold green]Goal:[/bold green] {task}\n")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as p:
        t = p.add_task("Running agent…", total=None)
        result = agent.run(task, verbose=True)
        p.update(t, completed=True)

    console.print("\n" + "─" * 60)
    console.print(Panel(Markdown(result["final_output"]), title="[bold green]✅ Result[/bold green]", border_style="green"))

    table = Table(title="Run Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Episode ID", result["episode_id"])
    table.add_row("Success", "✅" if result["success"] else "⚠️ Partial")
    table.add_row("Duration", f"{result['duration_seconds']}s")
    table.add_row("Sub-tasks", str(result["stats"]["total_sub_tasks"]))
    table.add_row("Failed", str(result["stats"]["failed"]))
    console.print(table)


def interactive_loop() -> None:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from app.agent.core import agent

    console = Console()
    console.print(
        Panel.fit("[bold blue]🤖 Agent OS — Interactive Mode[/bold blue]\n[dim]'exit' to quit | 'stats' for memory stats[/dim]", border_style="blue")
    )

    while True:
        try:
            task = input("\n>> ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Bye.[/red]")
            break
        if not task:
            continue
        if task.lower() in ("exit", "quit", "q"):
            break
        if task.lower() == "stats":
            from app.agent.memory import agent_memory
            console.print(agent_memory.get_stats())
            continue
        result = agent.run(task)
        console.print(Panel(Markdown(result["final_output"]), title="[bold green]Result[/bold green]", border_style="green"))


def run_api() -> None:
    import uvicorn
    from app.utils.config import config

    print(f"Starting Agent OS API → http://{config.api_host}:{config.api_port}")
    print("API docs → http://localhost:8000/docs")
    uvicorn.run("app.main:app", host=config.api_host, port=config.api_port, reload=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent OS Launcher")
    parser.add_argument("--api", action="store_true", help="Start FastAPI server")
    parser.add_argument("--task", "-t", type=str, help="Run a single task and exit")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive multi-task loop")
    args = parser.parse_args()

    if args.api:
        run_api()
    elif args.interactive:
        interactive_loop()
    elif args.task:
        run_cli(args.task)
    else:
        run_cli()
