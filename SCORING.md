# Scoring

## Overview

The **Validator** ensures the integrity and performance of miners in a decentralized network through a **scoring model**. This README highlights the `_score_miner` method, the role of challenges, LLM-generated synthetic prompts, and organic prompt responses in maintaining dynamic validation.

## Table of Contents

1. [Scoring Model](#scoring-model)
   - [_score_miner Method](#score_miner-method)
2. [Challenges](#challenges)
   - [Funds Flow Challenge](#funds-flow-challenge)
   - [Balance Tracking Challenge](#balance-tracking-challenge)
3. [LLM Synthetic Prompts](#llm-synthetic-prompts)
4. [Organic Usage](#organic-usage)

## Scoring Model

The **scoring model** evaluates and ranks miners based on performance and reliability, fostering a secure and efficient network.

### [_score_miner](https://github.com/blockchain-insights/blockchain-insights-subnet/blob/main/src/subnet/validator/validator.py#L35) Method

This method calculates layered miner scores based on:

**Layer 1: Response Evaluation**
   - **No Response:** Score = `0` for non-compliance.
   
**Layer 2: Challenge Outcomes**
   - **Two Failed Challenges:** Final Score = `0`.
   - **One Failed Challenge:** Final Score = `0.15`.
   - **All Challenges Passed:** Base Score = `0.3`.
   
**Layer 3: Query Validation**
   - **Positive LLM Validation:** A positive validation adds `0.15` to the base score, resulting in a total score of `0.45`.
   - **Negative LLM Validation:** Final Score = `0.3`.
   
**Layer 4: Organic Prompt Rewards**
   - **Score:** Between `0.45` and `1.00`, depending on the number of accepted organic prompt responses among all miner responses within the last 30 days.

## Challenges

Challenges assess miner data integrity and correctness and influence their scores.

### Funds Flow Challenge

- **Objective:** Validate transaction integrity.
- **Impact:** Success increases the score, while failure results in a reduction.

### Balance Tracking Challenge

- **Objective:** Verify the accuracy of account balance reporting.
- **Impact:** Accurate reporting increases the score, while inaccuracies reduce it.

## LLM Synthetic Prompts

The Validator uses LLMs to generate synthetic prompts that simulate typical user queries.

- **Prompt Generation:** LLMs generate contextual prompts to test different miner functions.
- **Response Validation:** The LLM checks if the miner's response adequately addresses the simulated user query.
- **Scoring Influence:** Correct responses increase scores, while errors result in penalties.

## Organic Usage

The Validator module continuously assesses miners, recalculating scores based on real-time performance.

- **Scoring Influence:** Higher scores lead to more rewards and influence within the network.
- **Dynamic Updates:** Scores adjust dynamically based on performance, ensuring only reliable miners maintain their influence in the network.
