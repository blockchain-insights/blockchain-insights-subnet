import re
from typing import Any, cast

from communex.client import CommuneClient
from communex.misc import get_map_modules


def raise_exception_if_not_registered(validator_key, modules):
    val_ss58 = validator_key.ss58_address
    if val_ss58 not in modules.keys():
        raise RuntimeError(f"key {val_ss58} is not registered in subnet")


def get_miners(client: CommuneClient, netuid: int) -> dict[str, dict[str, Any]]:
    modules = cast(dict[str, Any], get_map_modules(client, netuid=netuid, include_balances=False))
    for miner_key, miner_metadata in modules.items():
        if miner_metadata['stake'] < 100:
            yield miner_key, miner_metadata

IP_REGEX = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+")


def cut_to_max_allowed_weights(
        score_dict: dict[int, float], max_allowed_weights: int
) -> dict[int, float]:
    # sort the score by highest to lowest
    sorted_scores = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)

    # cut to max_allowed_weights
    cut_scores = sorted_scores[:max_allowed_weights]

    return dict(cut_scores)


def extract_address(string: str):
    return re.search(IP_REGEX, string)


def get_ip_port(modules_adresses: dict[int, str]):
    filtered_addr = {id: extract_address(addr) for id, addr in modules_adresses.items()}
    ip_port = {
        id: x.group(0).split(":") for id, x in filtered_addr.items() if x is not None
    }
    return ip_port