"""added_validator_key_to_receipts

Revision ID: 020
Revises: 019
Create Date: 2024-11-09 08:20:56.757921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '020'
down_revision: Union[str, None] = '019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM miner_receipts")
    op.add_column('miner_receipts', sa.Column('validator_key', sa.String(), nullable=False))
    op.create_index('idx_miner_receipts_miner_key_timestamp', 'miner_receipts', ['miner_key', 'timestamp'], unique=False, postgresql_using='btree')
    op.create_index('idx_miner_receipts_network_timestamp', 'miner_receipts', ['network', 'timestamp'], unique=False, postgresql_using='btree')
    op.create_index('idx_miner_receipts_timestamp', 'miner_receipts', ['timestamp'], unique=False, postgresql_using='btree')
    op.create_index('idx_miner_receipts_validator_key_timestamp', 'miner_receipts', ['validator_key', 'timestamp'], unique=False, postgresql_using='btree')
    op.drop_column('miner_receipts', 'accepted')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('miner_receipts', sa.Column('accepted', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.drop_index('idx_miner_receipts_validator_key_timestamp', table_name='miner_receipts', postgresql_using='btree')
    op.drop_index('idx_miner_receipts_timestamp', table_name='miner_receipts', postgresql_using='btree')
    op.drop_index('idx_miner_receipts_network_timestamp', table_name='miner_receipts', postgresql_using='btree')
    op.drop_index('idx_miner_receipts_miner_key_timestamp', table_name='miner_receipts', postgresql_using='btree')
    op.drop_column('miner_receipts', 'validator_key')
    # ### end Alembic commands ###