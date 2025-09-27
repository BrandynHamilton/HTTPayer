from httpayer import HTTPayerClient
import click
import json
import jinja2
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

HTTPAYER_API_KEY = os.getenv("HTTPAYER_API_KEY")

@click.group()
def cli():
    """HTTPayer CLI tool for making HTTP requests with payment handling."""
    pass

@cli.command()
@click.argument('method', type=str)
@click.argument('url', type=str)
@click.option('--headers', type=str, default='{}', help='JSON string of headers')
@click.option('--data', type=str, default=None, help='Request body data')
@click.option('--params', type=str, default='{}', help='JSON string of query parameters')
def call(method, url, headers, data, params):
    """Make an HTTP request."""
    headers = json.loads(headers)
    params = json.loads(params)
    client = HTTPayerClient()
    response = client.request(method, url, headers=headers, data=data, params=params)
    click.echo(response)

cli.add_command(call)

if __name__ == '__main__':
    cli()