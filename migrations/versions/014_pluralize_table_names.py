"""pluralize table names

Revision ID: 014
Revises: 013
Create Date: 2024-09-18 15:53:01.295219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '014'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Rename the existing tables
    op.rename_table('validation_prompt', 'validation_prompts')
    op.rename_table('validation_prompt_response', 'validation_prompt_responses')
    op.rename_table('challenge_balance_tracking', 'challenges_balance_tracking')
    op.rename_table('miner_discovery', 'miner_discoveries')
    op.rename_table('challenge_funds_flow', 'challenges_funds_flow')

    # Rename primary key constraints
    op.execute('ALTER TABLE validation_prompts RENAME CONSTRAINT pk__validation_prompt TO pk__validation_prompts')
    op.execute('ALTER TABLE validation_prompt_responses RENAME CONSTRAINT pk__validation_prompt_response TO pk__validation_prompt_responses')

    # Rename foreign key constraints
    op.execute('ALTER TABLE validation_prompt_responses RENAME CONSTRAINT fk__validation_prompt_response__prompt_id__validation_prompt TO fk__validation_prompt_responses__prompt_id__validation_prompts')

    # Rename primary and unique constraints for challenges_balance_tracking
    op.execute('ALTER TABLE challenges_balance_tracking RENAME CONSTRAINT pk__challenge_balance_tracking TO pk__challenges_balance_tracking')
    op.execute('ALTER TABLE challenges_balance_tracking RENAME CONSTRAINT uq__challenge_balance_tracking__block_height TO uq__challenges_balance_tracking__block_height')

    # Rename primary and unique constraints for challenges_funds_flow
    op.execute('ALTER TABLE challenges_funds_flow RENAME CONSTRAINT pk__challenge_funds_flow TO pk__challenges_funds_flow')
    op.execute('ALTER TABLE challenges_funds_flow RENAME CONSTRAINT uq__challenge_funds_flow__tx_id TO uq__challenges_funds_flow__tx_id')

    # Rename primary and unique constraints for miner_discoveries
    op.execute('ALTER TABLE miner_discoveries RENAME CONSTRAINT pk__miner_discovery TO pk__miner_discoveries')
    op.execute('ALTER TABLE miner_discoveries RENAME CONSTRAINT uq__miner_discovery__miner_key TO uq__miner_discoveries__miner_key')

    # No changes to miner_receipts and its constraints

def downgrade() -> None:
    # Reverse the table renaming during downgrade
    op.rename_table('validation_prompts', 'validation_prompt')
    op.rename_table('validation_prompt_responses', 'validation_prompt_response')
    op.rename_table('challenges_balance_tracking', 'challenge_balance_tracking')
    op.rename_table('miner_discoveries', 'miner_discovery')
    op.rename_table('challenges_funds_flow', 'challenge_funds_flow')

    # Rename primary key constraints back to their original names
    op.execute('ALTER TABLE validation_prompts RENAME CONSTRAINT pk__validation_prompts TO pk__validation_prompt')
    op.execute('ALTER TABLE validation_prompt_responses RENAME CONSTRAINT pk__validation_prompt_responses TO pk__validation_prompt_response')

    # Rename foreign key constraints back
    op.execute('ALTER TABLE validation_prompt_responses RENAME CONSTRAINT fk__validation_prompt_responses__prompt_id__validation_prompts TO fk__validation_prompt_response__prompt_id__validation_prompt')

    # Rename primary and unique constraints for challenges_balance_tracking back
    op.execute('ALTER TABLE challenges_balance_tracking RENAME CONSTRAINT pk__challenges_balance_tracking TO pk__challenge_balance_tracking')
    op.execute('ALTER TABLE challenges_balance_tracking RENAME CONSTRAINT uq__challenges_balance_tracking__block_height TO uq__challenge_balance_tracking__block_height')

    # Rename primary and unique constraints for challenges_funds_flow back
    op.execute('ALTER TABLE challenges_funds_flow RENAME CONSTRAINT pk__challenges_funds_flow TO pk__challenge_funds_flow')
    op.execute('ALTER TABLE challenges_funds_flow RENAME CONSTRAINT uq__challenges_funds_flow__tx_id TO uq__challenge_funds_flow__tx_id')

    # Rename primary and unique constraints for miner_discoveries back
    op.execute('ALTER TABLE miner_discoveries RENAME CONSTRAINT pk__miner_discoveries TO pk__miner_discovery')
    op.execute('ALTER TABLE miner_discoveries RENAME CONSTRAINT uq__miner_discoveries__miner_key TO uq__miner_discovery__miner_key')

    # No changes to miner_receipts and its constraints
