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
- Appendix
  - [History of the Chain Insights Subnet](#History-of-the-Chain-Insights-Subnet)
  - [Guru Posdast with aphex5](#Guru-Posdast-with-aphex5)
  
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


#Appendix

## History of the Chain Insights Subnet

**Formation and Launch**

Chain Insights Subnet was formally registered on the Bittensor network on October 25, 2023. The subnet became operational in the first days of December 2023. It was founded by **aphex5**, a well-known figure in the community. From its inception, Chain Insights aimed to provide comprehensive analytics for tracking and analyzing cryptocurrency fund flows and balance changes, offering valuable insights into the cryptocurrency ecosystem, detecting anomalies, and combating financial crimes.

**Early Growth and Team Expansion**

The project quickly garnered attention and support from validators, bolstered by growing emissions. At the beginning of the first quarter (Q1) of 2024, the subnet team expanded by adding six new developers. This growth continued into the second quarter (Q2) with the addition of four more developers, bringing fresh expertise and momentum to the project.

**Shift in Development Priorities**

However, during Q2, Chain Insights faced significant challenges that necessitated a shift in development priorities. The primary stressor was the **Open Tensor Foundation (OTF)**, which demanded more diversified miner metrics, benchmarking, and monitoring. These requirements diverted the team's focus away from developing core product functionalities.

Subsequent demands from the OTF included transforming miners into producers of "commodities," which required integrating additional AI components into the miner side. This shift was not aligned with Chain Insights' original product vision. As a result, the team struggled to achieve success in these new areas. The OTF's requirements were constantly evolving, starting with requests to "copy some other blockchain in the form of a subnet," then stipulating that 20% of miners must be the best performers while the remaining 80% could be less efficient, and later insisting that miners produce tangible goods.

**Challenges and Deregistration**

Despite efforts to adapt, Chain Insights was unable to meet the ever-changing demands set by the OTF. By August 25, 2024, the subnet faced deregistration. Prior to this, the team had implemented several features, including Chain Chat, large language model (LLM) conversions to Cypher/SQL queries, and miner/validator monitoring, miner performance benchmarking. However, these efforts were insufficient to satisfy the OTF's requirements.

Compounding these challenges, the judges from the OTF frequently changed, bringing new judgment rules and a lack of understanding of Chain Insights' objectives. They questioned the subnet's focus, asking why it did not monitor social media or why it was positioned as a blockchain explorer.

**Transition to Commune AI**

In response to these obstacles, the Chain Insights team decided to transition to Commune AI. This move allowed them to develop their subnet independently, free from the influence of the OTF. By doing so, they aim to pursue their original vision without being subjected to the constantly changing directives of a major governing party.

**Current Vision**

Today, Chain Insights continues to focus on its core mission of providing advanced analytics for cryptocurrency fund flows and balance changes. The team is dedicated to delivering valuable insights into the cryptocurrency ecosystem, enhancing anomaly detection, and strengthening efforts to combat financial crimes. By operating within Commune AI, Chain Insights strives to maintain its autonomy and stay true to its foundational goals, fostering innovation and reliability in the blockchain analytics space.

## Guru Podcast with aphex5

- [Listen on spotify](https://open.spotify.com/episode/62k9rmnWWCWHf8bvawpO6R?si=WJcJPM0BSmmSSDWsm5T4EQ&nd=1&dlsi=368afd1dbeb149dd)
- [Wath on X platform](https://x.com/KeithSingery/status/1768303479741898862?s=20)

## Chain Chat early days demo
- [Watch on loom](https://www.loom.com/share/4ef89f1952a542a88968cd24578e1f43?sid=49f08f16-52a9-44e4-90d5-74bdd533a30d)