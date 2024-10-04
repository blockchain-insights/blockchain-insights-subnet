<div style="display: flex; align-items: center;">
  <img src="docs/subnet_logo.png" alt="subnet_logo" style="width: 60px; height: 60px; margin-right: 10px;">
  <h1 style="margin: 0;">Chain Insights Subnet</h1>
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
- Appendix
  - [History of the Chain Insights Subnet](#History-of-the-Chain-Insights-Subnet)
  - [Guru Posdast with aphex5](#Guru-Posdast-with-aphex5)
  
### Subnet Vision

The Subnet aims to deliver comprehensive insights into cryptocurrency fund flows and balance changes, presented in a user-friendly manner. It is designed to:

- **Provide Funds Flow and Balance Insights**: Offer detailed tracking and analysis of cryptocurrency movements and balances.
- **Detect Anomalies**: Identify suspicious activities and irregularities that may indicate fraud, scams, rug pulls, or money laundering.
- **Combat Financial Crimes**: Assist in the early detection and prevention of financial crimes, including money laundering, fraud, and other illicit activities within the cryptocurrency ecosystem.

This subnet continues the legacy of the blockchain data insights subnet from the Bittensor ecosystem, but with its root vision from 25th October 2023.

The **Chain Insights Subnet** introduces a new category of software, known as a *Funds Flow Explorer*.
It focuses on tracking and analyzing the movement of cryptocurrency funds and changes in balances. Unlike traditional blockchain explorers or node providers, Chain Insights offers deep, actionable insights into the ecosystem, helping detect anomalies and combat financial crimes, while empowering users with a comprehensive understanding of cryptocurrency flows.
 
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


# Appendix

## History of the Chain Insights Subnet
### Formation and Launch

Chain Insights Subnet officially launched on the Bittensor network on October 25, 2023, becoming fully operational in early December 2023. Founded by aphex5, a respected figure in the community, Chain Insights was created to deliver powerful, in-depth analytics for tracking and analyzing cryptocurrency fund flows and balance changes. The goal has always been to provide valuable insights into the cryptocurrency ecosystem, enhance anomaly detection, and contribute to the fight against financial crimes.

### Early Growth and Team Expansion

The project quickly gained momentum, attracting strong support from validators and benefiting from increasing emissions. By Q1 2024, the team had grown with the addition of six talented developers, further fueling the project's growth. In Q2 2024, the team welcomed four more developers, bringing new skills and ideas to help accelerate innovation and development.

### Adapting to New Opportunities

During Q2, the evolving needs of the Open Tensor Foundation (OTF) presented exciting new opportunities for Chain Insights. The OTF’s focus on more diversified miner metrics and AI-driven advancements pushed the team to explore new frontiers, integrating advanced technologies and enhancing the miner-side functionality. This phase allowed the team to broaden its expertise and experiment with new concepts, further strengthening Chain Insights' capabilities.

### Overcoming Challenges and Looking Ahead

As the project navigated these changes, Chain Insights delivered several key features, including Chain Chat, Cypher/SQL query conversions using large language models (LLMs), and tools for miner/validator monitoring and performance benchmarking. These developments reflected the team’s dedication to innovation and their commitment to creating a robust analytical tool for the cryptocurrency ecosystem.

While the constantly evolving requirements from the OTF posed challenges, they also helped sharpen the team's focus and clarify the subnet’s unique value proposition. The team's resilience and vision have ensured that Chain Insights remains true to its original mission.

### Transition to Commune AI

In August 2024, Chain Insights made a strategic decision to transition to Commune AI, an independent platform that allows the team to pursue their vision without external constraints. This move enables the team to continue refining the Chain Insights Subnet and deliver on its promise of providing advanced, cutting-edge analytics for cryptocurrency fund flows and balance changes.

Current Vision

Today, Chain Insights remains focused on its core mission: offering comprehensive insights into cryptocurrency ecosystems, enhancing anomaly detection, and strengthening efforts to combat financial crimes. Operating within the Commune AI ecosystem allows the team to maintain autonomy and push forward with innovation, ensuring that Chain Insights remains a leader in blockchain analytics while staying true to its foundational goals.

## Guru Podcast with aphex5

- [Listen on spotify](https://open.spotify.com/episode/62k9rmnWWCWHf8bvawpO6R?si=WJcJPM0BSmmSSDWsm5T4EQ&nd=1&dlsi=368afd1dbeb149dd)
- [Wath on X platform](https://x.com/KeithSingery/status/1768303479741898862?s=20)

## Chain Chat early days demo
- [Watch on loom](https://www.loom.com/share/4ef89f1952a542a88968cd24578e1f43?sid=49f08f16-52a9-44e4-90d5-74bdd533a30d)