<div style="display: flex; align-items: center;">
  <img src="docs/subnet_logo.png" alt="subnet_logo" style="width: 60px; height: 60px; margin-right: 10px;">
  <h1 style="margin: 0;">Chain Insights</h1>
</div>

## Table of Contents
 
- [Introduction](#introduction)
- [Subnet Vision](#subnet-vision)
- [Roadmap](#roadmap)
- [Overview](#overview)
- [Subnet Architecture Components](#subnet-architecture-components)
- [Scoring](#scoring)
- [Miner Setup](MINER_SETUP.md)
- [Validator Setup](VALIDATOR_SETUP.md)

### Subnet Vision

The Subnet aims to deliver comprehensive insights into cryptocurrency fund flows and balance changes, presented in a user-friendly manner. It is designed to:

- **Provide Funds Flow and Balance Insights**: Offer detailed tracking and analysis of cryptocurrency movements and balances.
- **Detect Anomalies**: Identify suspicious activities and irregularities that may indicate fraud, scams, rug pulls, or money laundering.
- **Combat Financial Crimes**: Assist in the early detection and prevention of financial crimes, including money laundering, fraud, and other illicit activities within the cryptocurrency ecosystem.

This subnet continues the legacy of the blockchain data insights subnet from the Bittensor ecosystem, but with its root vision from 25th October 2023.

Key points to note:
  - **Chain Insights** is NOT a blockchain node provider
  - **Chain Insights** is NOT a blockchain explorer. Although there may be some similarities, we focus on visualizing the flow of money.
  - **Chain Insights** is not a social media scraper, nor a media sentiment analysis tool.
  - **Chain Insights** is not an API service for blockchain data retrieval (it's not like The Graph protocol or SubQuery).
  
  **Chain Insights** is an analytical subnet that enables the tracking and analysis of cryptocurrency fund flows and balance changes. It is designed to provide comprehensive insights into the cryptocurrency ecosystem, detect anomalies, and combat financial crimes.

### Roadmap

- [x] **Migration from Bittensor**: Transition the subnet from the Bittensor ecosystem to a commune ai ecosystem.
- [ ] **Funds flow api**: Develop a funds flow API that provides detailed insights into cryptocurrency fund flows.
- [ ] **Balance API**: Create a balance API that tracks changes in cryptocurrency balances.
- [ ] **Data Visualization**: Implement data visualization tools to present insights in a user-friendly format.
- [ ] **App Development programme**: Launch an app development program to encourage the creation of applications that leverage the chain insights.
- [ ] **Blockchain network monitoring**: Use miners with AI models to analyze blockchain data in real time to detect malicious funds flow patterns.
- [ ] **Network Integrations**: Ongoing Miner's developments of blockchain indexers for various blockchain networks.
  - [ ] **Commune AI Integrations**
  - [ ] **Bittensor In Integration**
  - [ ] **Ethereum Integration**
  

### Overview

### Subnet Architecture Components

**1. Subnet Owner**:
   - **Role & Responsibilities**: Subnet Owner acts as the coordinator and facilitator of the network. He is responsible for the overall development and maintenance of the subnet, collaborating with miners and validators to ensure the network's success.

**2. Validators**:
   - **Role & Responsibilities**: Validators are crucial for maintaining the integrity and accuracy of miners' work. They host APIs that allow interaction and integration with the subnet.

**3. Miners**:
   - **Role & Responsibilities**: Miners are responsible for indexing blockchain data and providing access to validators via APIs. They also participate in AI model training to detect anomalies in the data.

These components work together in a collaborative ecosystem, with each playing a vital role in the subnets operation and evolution.

### Scoring

The **Validator** ensures the integrity and performance of miners in a decentralized network through a **scoring model**. This README highlights the `_score_miner` method, the role of challenges, LLM-generated synthetic prompts, and organic prompt responses in maintaining dynamic validation.

#### Scoring Model

The **scoring model** evaluates and ranks miners based on performance and reliability, fostering a secure and efficient network.

#### [_score_miner](https://github.com/blockchain-insights/blockchain-insights-subnet/blob/main/src/subnet/validator/validator.py#L35) Method

This method calculates layered miner scores based on:

**Layer 1: Response Evaluation**
   - **No Response:** Score = `0` for non-compliance.
   
**Layer 2: Challenge Outcomes**
   - **Two Failed Challenges:** Final Score = `0`.
   - **One Failed Challenge:** Final Score = `0.15`.
   - **All Challenges Passed:** Base Score = `0.3`.

**Layer 3: Organic Prompt Rewards**
   - **Score:** Between `0.3` and `1.00`, depending on the number of accepted organic prompt responses among all miner responses within the last 30 days.

**Layer 4 - WHEN Ready**
  - Provides additional scoring for malicious pattern detection and blockchain monitoring alerts.

## Challenges

Challenges assess miner data integrity and correctness and influence their scores.

### Funds Flow Challenge

- **Objective:** Validate transaction integrity.
- **Impact:** Success increases the score, while failure results in a reduction.

### Balance Tracking Challenge

- **Objective:** Verify the accuracy of account balance reporting.
- **Impact:** Accurate reporting increases the score, while inaccuracies reduce it.

## Organic Usage

The Validator module continuously assesses miners, recalculating scores based on real-time performance.

- **Scoring Influence:** Higher scores lead to more rewards and influence within the network.
- **Dynamic Updates:** Scores adjust dynamically based on performance, ensuring only reliable miners maintain their influence in the network.
