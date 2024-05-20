"""make player tg id biginteger

Revision ID: 81546d951a1a
Revises: 537a3e19c80d
Create Date: 2024-05-16 13:47:14.958728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81546d951a1a'
down_revision: Union[str, None] = '537a3e19c80d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('players', 'tg_id',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('players', 'tg_id',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    # ### end Alembic commands ###
