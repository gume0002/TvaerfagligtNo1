from alembic import context

from app.config import Settings
from app.data_access.database import create_database_engine
from app.data_access.orm_models import Base


def run_migrations():
    engine = create_database_engine(Settings.from_env())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations()
