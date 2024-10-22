import datetime
from loguru import logger
from typing import List, Dict, Any
from src.subnet.validator_api.models import BaseChartTransformer

class BitcoinChartTransformer(BaseChartTransformer):

    def is_chart_applicable(self, data: List[Dict[str, Any]]) -> bool:
        # Check if the data contains entries with 'block', 'block_height', 'in_total_amount', or 'out_total_amount' for funds flow
        funds_flow_applicable = any(
            ('in_total_amount' in entry or 'out_total_amount' in entry or
             ('t1' in entry and ('in_total_amount' in entry['t1'] or 'out_total_amount' in entry['t1'])))
            for entry in data
        )

        # Check if the data contains entries with 'block' or 'block_height' or 'balance'/'d_balance' for balance tracking
        balance_tracking_applicable = any(
            ('address' in entry and ('block' in entry or 'block_height' in entry or 'balance' in entry or 'd_balance' in entry))
            for entry in data
        )

        return funds_flow_applicable or balance_tracking_applicable

    def convert_balance_tracking_to_chart(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        relevant_entries = []

        # Extract relevant data
        for entry in data:
            if 'address' in entry and ('balance' in entry or 'd_balance' in entry or 'block' in entry or 'block_height' in entry):
                relevant_entries.append(entry)

        # Log the relevant entries
        logger.info(f"Relevant entries for chart conversion: {relevant_entries}")

        labels = [entry['address'] for entry in relevant_entries]
        balances = [entry.get('balance', entry.get('d_balance')) for entry in relevant_entries]
        blocks = [entry.get('block', entry.get('block_height')) for entry in relevant_entries]

        # Log the extracted data
        logger.info(f"Labels: {labels}")
        logger.info(f"Balances: {balances}")
        logger.info(f"Blocks: {blocks}")

        datasets = []
        if any(balances):
            datasets.append({
                "label": "Balance",
                "data": [b if b is not None else 0 for b in balances]  # Handle None values
            })
        if any(blocks):
            datasets.append({
                "label": "Block",
                "data": [bh if bh is not None else 0 for bh in blocks]  # Handle None values
            })

        # Log the datasets
        logger.info(f"Datasets: {datasets}")

        chart_data = {
            "chart_type": "bar",
            "labels": labels,
            "datasets": datasets
        }

        return [chart_data]  # Ensure it returns a list

    def convert_funds_flow_to_chart(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        relevant_entries = []

        # Extract relevant data from the structure
        for entry in data:
            if 'in_total_amount' in entry or 'out_total_amount' in entry:
                relevant_entries.append(entry)
            elif 't1' in entry:
                transaction = entry['t1']
                if 'in_total_amount' in transaction or 'out_total_amount' in transaction:
                    relevant_entries.append(transaction)

        # Log the relevant entries
        logger.info(f"Relevant entries for chart conversion: {relevant_entries}")

        # Sort entries by timestamp if available, otherwise by block/block_height
        sorted_entries = sorted(relevant_entries, key=lambda x: x.get('timestamp'))

        # Extract data for chart
        labels = [f"Transaction {i+1}" for i in range(len(sorted_entries))]
        in_total_amounts = [entry.get('in_total_amount', None) for entry in sorted_entries]
        out_total_amounts = [entry.get('out_total_amount', None) for entry in sorted_entries]

        # Log the extracted data
        logger.info(f"Labels: {labels}")
        logger.info(f"In Total Amounts: {in_total_amounts}")
        logger.info(f"Out Total Amounts: {out_total_amounts}")

        datasets = []
        if any(in_total_amounts):
            datasets.append({
                "label": "In Total Amount",
                "data": [in_amt if in_amt is not None else 0 for in_amt in in_total_amounts]  # Handle None values
            })
        if any(out_total_amounts):
            datasets.append({
                "label": "Out Total Amount",
                "data": [out_amt if out_amt is not None else 0 for out_amt in out_total_amounts]  # Handle None values
            })

        # Log the datasets
        logger.info(f"Datasets: {datasets}")

        chart_data = {
            "chart_type": "bar",
            "labels": labels,
            "datasets": datasets
        }

        return [chart_data]  # Ensure it returns a list