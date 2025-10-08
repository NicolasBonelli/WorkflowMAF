# WorkflowMAF

# 🧠 Mini Project — Workflow with Microsoft Agent Framework (Python)

## 📘 Description

This project demonstrates the practical use of the **Microsoft Agent Framework** in **Python**, building an **intelligent workflow** that combines conditional logic (branching / switch) and a sequential chain of agents.  
The goal is to showcase how to orchestrate multiple agents that collaborate to handle different types of user requests, simulating a simple corporate environment (e.g., IT Support or Human Resources).

---

## ⚙️ Technologies and Libraries

- **Microsoft Agent Framework (Python SDK)** — core for agent orchestration and workflow management.  
- **Azure OpenAI (GPT-4.1)** — model used by agents for reasoning and generating responses.  
- **Pydantic** — structured model definition and response validation.  
- **Python 3.10+**  
---

## 🧩 Workflow Architecture

```mermaid
flowchart TD
    A[👤 User] --> B[🤖 TypeClassifierAgent]
    B --> C{SwitchNode(request_type)}
    C -->|technical| D1[🧰 DiagnosticAgent]
    D1 --> D2[🔧 SolutionAgent (uses a Tool)]
    C -->|hr| E[🧾 HumanResourcesAgent]
    C -->|other| F[💬 GenericMessageNode]
    D2 --> G[(📤 Final Output)]
    E --> G
    F --> G
