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

JSONEXT = '.json'
TOMLEXT = '.toml'
command = string.Template('$editor $filename')


import jsondb

import toml
from rich.console import Console
from rich.panel import Panel

import typer

app = typer.Typer()
console = Console()
color = "white"

columns = shutil.get_terminal_size().columns - 6

# template
'''
[[-]]
quote = ''
author = ''
reference = ''
tags = []
'''
quotes_template = {
	'-': [
		{
			'quote': '',
			'author': '',
			'reference': '',
			'tags': []
		}
	]
}

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

def environ_present(key='EDITOR'):
	return key in os.environ

def open_temp_toml_file():
	if environ_present('EDITOR'):
		editor = os.environ['EDITOR']
		fd, filename = tempfile.mkstemp(suffix=TOMLEXT, text=True)
		with open(filename, 'w') as file:
			toml.dump(quotes_template, file)
		write_status = subprocess.call(
			command.substitute(editor=editor, filename=filename), 
			shell=True
		)
		if write_status != 0:
			os.remove(filename)
		return filename, write_status
	else:
		raise Exception('EDITOR not found in env')

@app.command()
def add():
	filetype = '.toml'
	filename, status = open_temp_toml_file()
	default_author = 'Anonymous'
	default_reference = 'Unknown'
	total_quotes = 0
	if status == 0:
		with open(filename, 'r') as file:
			quotes = toml.load(file)
			total_quotes = len(quotes.get('-'))
			for quote in quotes.get('-'):
				if not quote.get('quote'):
					console.print('[red bold]quote not added')
					sys.exit()
				db.insert(
					[
						{
							"quote": quote.get('quote'),
							"author": quote.get('author') or default_author,
							"reference": quote.get('reference') or default_reference,
							"tags": quote.get('tags'),
							"added_date": str(datetime.datetime.now()),
						}
					]
				)
		db.dump()
		console.print('[green bold]{} {} added'.format(total_quotes, 'quote' if total_quotes==1 else 'quotes'))

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
