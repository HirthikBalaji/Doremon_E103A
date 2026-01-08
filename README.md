# Methodology

## 1. Core Contribution Equation (High-Level)

$$
\boxed{
\text{Contribution Score (CS)} =
\Big( \sum_{i=1}^{N} W_i \cdot A_i \Big)
\times Q
\times C
\times P 
-
B
}
$$

This keeps it **modular, explainable, and tunable**.

---

## 2. Base Work Done (Activity Contribution)

$$
\text{Base Work} = \sum_{i=1}^{N} W_i \cdot A_i
$$

Where:

* ($A_i$) = Count or intensity of activity type *i*
* ($W_i$) = Weight for that activity

### Example Activity Variables

| Activity ($A_i$) | Description              |
|------------------| ------------------------ |
| ($A_1$)          | Tasks completed (Jira)   |
| ($A_2$)          | Code commits             |
| ($A_3$)          | PRs merged               |
| ($A_4$)          | Meetings led             |
| ($A_5$)          | Design docs / proposals  |
| ($A_6$)          | Mentoring / reviews done |

---

## 3. Quality Multiplier (Peer Review + Outcomes)

$$
Q = 1 + \alpha \cdot R + \beta \cdot S
$$

Where:

* (R) = Peer review score (0–1 or 1–5 normalized)
* (S) = Stability / success rate (bug-free releases, acceptance rate)
* ($\alpha, \beta$) = Tunable impact factors

📌 *Ensures quality > quantity*

---

## 4. Collaboration & Knowledge Sharing Factor

$$
C = 1 + \gamma \cdot K
$$

Where:

* (K) = Knowledge contribution index
  (helping teammates, answering Slack threads, docs, unblocking others)

---

## 5. Peer Recognition / Kudos Factor

$$
P = 1 + \delta \cdot \log(1 + U)
$$

Where:

* (U) = Peer kudos / endorsements
* Log prevents popularity bias
* ($\delta$) controls recognition influence

---

## 6. Blocker & Friction Penalty

$$
B = \lambda_1 \cdot D + \lambda_2 \cdot F + \lambda_3 \cdot R_w
$$ 

Where:

* ($D$) = Delays caused
* ($F$) = Rework or rejected submissions
* ($R_w$) = Repeated unresolved blockers
* ($\lambda$) = penalty weights

🚨 *Penalizes friction, not silence*

---

## 7. Optional Impact Scaling (Business Value)

$$
\text{Final Score} =
CS \times (1 + \theta \cdot I)
$$

Where:

* (I) = Business impact (revenue, customer impact, risk reduction)

---

## 8. Compact General Formula (Production-Friendly)

$$
\boxed{
\text{CS} =
\Big( \sum W_i A_i \Big)
\cdot
(1 + \alpha R + \beta S)
\cdot
(1 + \gamma K)
\cdot
(1 + \delta \log(1 + U))
;-;
\sum \lambda_j P_j
}
$$

---

## 9. Why This Model Works Well (Important)

* Role-agnostic (engineer, manager, designer)
* Resistant to gaming
* AI-friendly (features from Slack, GitHub, Jira)
* Explainable to HR & leadership
* Encourages collaboration over noise

---

