#!/usr/bin/env python

# fredson - a minimal computing utility for creating and publishing
# BIBFRAME-conformant bibliographical datasets

# Modeled on Hugo and implemented using Datasette

import click, glob, yaml, shutil, os
from pathlib import Path
from slugify import slugify
from sqlite_utils import Database
from PIL import Image

def load_data(db, type):
    for yml_file in Path('.').glob(f'./data/{type}s/**/*.yml'):
        obj = yaml.load(yml_file.read_text(), Loader=yaml.Loader)
        db[f'{type}s'].upsert(obj, pk='id')

def uniquify(type, slug):
    n = 0
    while True:
        n += 1
        dir = f'./data/{type}s/{slug}-{n}'
        if not Path(dir).exists():
            return f'{slug}-{n}'

# this should be in profiles/config
def stub_metadata(type, identifier, title):
    if type == 'item':
        return f'id: {identifier}\ncreator: \ntitle: >\n  {title}\npublisher: >\ndate: \nitemOf: \ndescription: >'
    elif type == 'instance':
        return f'id: {identifier}\ncreator: \ntitle: >\n  {title}\ninstanceOf: \ndescription: >'
    elif type == 'work':
        return f'id: {identifier}\ncreator: \ntitle: >\n  {title}\ndescription: >'
    elif type in ['agent', 'event', 'subject']:
        return f'id: {identifier}\ntitle: >\n  {title}\ndescription: >'
    else:
        return f'id: {identifier}\ntitle: >\n  {title}\ndescription: >'

@click.group()
def cli():
    pass

# option to new from import of csv file?
@click.command()
@click.argument('name')
def new(name):
    # create default directory structure
    Path(f'./{name}').mkdir()
    Path(f'./{name}/data').mkdir()
    Path(f'./{name}/data/items').mkdir()
    Path(f'./{name}/data/instances').mkdir()
    Path(f'./{name}/data/works').mkdir()
    Path(f'./{name}/data/agents').mkdir()
    Path(f'./{name}/data/events').mkdir()
    Path(f'./{name}/data/subjects').mkdir()
    # generate default config yml_file
    Path(f'./{name}/config.yml').write_text('---\n\n')
    click.echo(f'Created {name}')

@click.command()
@click.argument('name')
def remove(name):
    # delete directory tree starting from dataset directory
    shutil.rmtree(f'./{name}')
    click.echo(f'Removed {name}')

@click.command()
@click.argument('type')
@click.argument('name')
def add(type, name):
    # should we just take the supplied name and warn user if there's a collision?
    identifier = uniquify(type, slugify(name)[:30])
    Path(f'./data/{type}s/{identifier}').mkdir()
    Path(f'./data/{type}s/{identifier}/metadata.yml').write_text(stub_metadata(type, identifier, name))
    click.echo(f'Added {type} {identifier}')

@click.command()
def validate():
    # run yamllint to flag any poorly formed YAML
    os.system('yamllint .')

@click.command()
def build():
    # foreign keys resolve?
    db = Database("catalog.db", recreate=True)
    items = db["items"].create({
        "id": str,
        "creator": str,
        "title": str,
        "publisher": str,
        "date": str,
        "itemOf": str,
        "description": str,
        }, pk="id")
    load_data(db, "item")
    click.echo('Generated catalog.db')

@click.command()
def server():
    # run datasette server to serve locally
    os.system('datasette catalog.db')

@click.command()
@click.argument('service')
def publish(service):
    # run datasette publish cloudrun to push data to GCP
    os.system(f'datasette publish cloudrun catalog.db --service {service}')

@click.command()
def version():
    # initialize off of package metadata?
    click.echo('Fredson 0.1')

cli.add_command(new)
cli.add_command(remove)
cli.add_command(add)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(server)
cli.add_command(publish)
cli.add_command(version)

if __name__ == '__main__':
    cli()
