import random
import pathlib
import datetime
import shutil
import sys
import os
import subprocess
import tempfile
import string
from typing import Optional

from jsondb import jsondb
from jsondb import DuplicateEntryError

import typer
import toml
from rich.console import Console


command = string.Template("$editor $filename")
date_format = "%a %d %b %Y %X"


app = typer.Typer()
console = Console()


# template
"""
[[-]]
quote = ''
author = ''
reference = ''
tags = []
"""
quotes_template = {"-": [{"quote": "", "author": "", "reference": "", "tags": []}]}


def display_quote(quote):
    console.print("\n\n")
    console.print(
        "“{quote}” ── [yellow]{author}[/]\n\n [blue]({reference})[/]\n\n[grey46]{date}[/]\n\n".format(
            quote=quote.get("quote"),
            author=quote.get("author"),
            reference=quote.get("reference") or "Unknown",
            date=quote.get("added_date") or "",
        ),
        justify="center",
    )


def environ_present(key="EDITOR"):
    return key in os.environ


def open_temp_toml_file():
    if environ_present("EDITOR"):
        editor = os.environ["EDITOR"]
        fd, filename = tempfile.mkstemp(suffix=".toml", text=True)
        with open(filename, "w") as file:
            toml.dump(quotes_template, file)
        write_status = subprocess.call(
            command.substitute(editor=editor, filename=filename), shell=True
        )
        if write_status != 0:
            os.remove(filename)
        return filename, write_status
    else:
        raise Exception("EDITOR not found in env")


def insert(quotes):
    total_quotes = len(quotes.get("-"))
    for quote in quotes.get("-"):
        if not quote.get("quote"):
            console.print("[red bold]quote not added")
            sys.exit()
        try:
            db.insert(
                [
                    {
                        "quote": quote.get("quote"),
                        "author": quote.get("author") or "anonymous",
                        "reference": quote.get("reference") or "unknown",
                        "tags": quote.get("tags"),
                        "added_date": datetime.datetime.now().strftime(date_format),
                    }
                ]
            )
        except DuplicateEntryError as e:
            console.print("[red]Duplicate quote found")
            sys.exit()
    console.print(
        "[green bold]{} {} added".format(
            total_quotes, "quote" if total_quotes == 1 else "quotes"
        )
    )


@app.command()
def new():
    filetype = ".toml"
    filename, status = open_temp_toml_file()
    total_quotes = 0
    if status == 0:
        with open(filename, "r") as file:
            quotes = toml.load(file)
            insert(quotes)


@app.command()
def ls(order: str = typer.Argument("recent"), val: int = typer.Argument(10)):
    if order not in ["recent", "past"]:
        raise Exception("order has to be either (recent | past)")
    all_quotes = db.find(lambda x: True)
    ordered_latest = sorted(
        all_quotes,
        key=lambda i: datetime.datetime.strptime(i["added_date"], date_format),
        reverse=True,
    )
    if order == "recent":
        for quote in ordered_latest[:val]:
            display_quote(quote)
    else:
        for quote in ordered_latest[-val:]:
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
    dbroot = pathlib.Path.home() / ".local/quote"
    dbroot.mkdir(parents=True, exist_ok=True)
    db = jsondb(str(pathlib.Path(dbroot / "quotes.json")))
    db.set_index("quote")
    return db


db = init_db()
if __name__ == "__main__":
    app()
