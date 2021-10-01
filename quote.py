import random
import pathlib
import datetime
import shutil

import jsondb

from rich.console import Console
from rich.panel import Panel

import typer

app = typer.Typer()
console = Console()
color = "white"

columns = shutil.get_terminal_size().columns - 6


def display_quote(quote):
    console.print(
        Panel(
            """[{color}]{}[/{color}]\n\n[italic {color}]{}\n{}[/italic {color}]""".format(
                quote.get("quote"),
                quote.get("author").rjust(columns, " "),
                quote.get("reference").rjust(columns, " "),
                color=color,
            ),
        ),
        style=color,
    )


@app.command()
def add():
    quote = input("quote: ")
    author = input("author: ") or "anonymous"
    reference = input("reference: ") or "unknown"
    tags = input("tags: ") or "default"
    db.insert(
        [
            {
                "quote": quote,
                "author": author,
                "reference": reference,
                "tags": list(map(str.strip, tags.split(","))),
                "added_date": str(datetime.datetime.now()),
            }
        ]
    )
    db.dump()


@app.command("list")
def ls(order: str, val: int = typer.Argument("10")):
    if order not in ["first", "last"]:
        raise Exception('order has to be either "first" or "last"')
    all_quotes = db.find(lambda x: True)
    ordered_latest = sorted(all_quotes, key=lambda i: i['added_date'], reverse=True) 
    if order == "first":
        for quote in all_quotes[:val]:
            display_quote(quote)
    else:
        for quote in all_quotes[-val:]:
            display_quote(quote)


@app.command()
def tag(tagstr: str):
    quotes = db.find(lambda x: tagstr in x.get("tags"))
    for quote in quotes:
        display_quote(quote)


@app.command()
def author(author: str):
    quotes = db.find(lambda x: author == x.get("author"))
    for quote in quotes:
        display_quote(quote)


@app.command("random")
def rand():
    all_quotes = db.find(lambda x: True)
    total_quotes = len(all_quotes)
    quote = all_quotes[random.randrange(0, total_quotes, 1)]
    display_quote(quote)


def init_db():
    dbroot = pathlib.Path.home() / ".config/quote"
    dbroot.mkdir(parents=True, exist_ok=True)
    DBNAME = "quotes"
    dbpath = pathlib.Path(dbroot / "quotes.json")
    db = jsondb.load(str(dbroot))
    if not dbpath.exists():
        return db.new("quotes")
    return db.get("quotes")


db = init_db()
if __name__ == "__main__":
    app()
