from sqlmodel import SQLModel

from bluetext.postgres_client import PostgresClient

from ..db import models
import ..conf

def init_postgres(app):

    postgres_config = conf.get_postgres_conf()
    pool_config = conf.get_postgres_pool_conf()
    app.state.postgres_client = PostgresClient(postgres_config, pool_config)
    await app.state.postgres_client.initialize()
    await app.state.postgres_client.init_connection()

    # Create tables after connection is established
    await app.state.postgres_client.create_tables(SQLModel.metadata)

def deinit_postgres(app):
    await app.state.postgres_client.close()
