import click
from flask.cli import with_appcontext
from .db import init_db as init_db_function
from .seeder import seed_data
from .extensions import db

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    db.create_all()
    init_db_function()
    click.echo('Initialized the database.')

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seeds the database with a large amount of test data."""
    seed_data()
    click.echo('Database seeded with test data.')

def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)

