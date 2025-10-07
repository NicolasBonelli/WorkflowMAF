# 🧠 Mini Proyecto — Workflow con Microsoft Agent Framework (Python)

## 🎯 Objetivo

Este proyecto tiene como objetivo demostrar el uso práctico del **Microsoft Agent Framework** en Python a través de un **workflow con branching logic (switch)** y una **rama secuencial de agentes**.  
Será un ejemplo compacto pero funcional, ideal para mostrar a supervisores o compañeros cómo se puede orquestar lógica condicional y secuencial entre agentes.

---

## ⚙️ Tecnologías y Librerías

- **Microsoft Agent Framework (Python SDK)** → núcleo del sistema de orquestación de agentes.  
- **Pydantic** → definición de modelos estructurados para el parsing de respuestas de agentes.  
- **Python 3.10+** → lenguaje base del proyecto.  
- **(Opcional)**: alguna **tool simple** (por ejemplo, una función o endpoint local) usada por el agente final para obtener información o ejecutar una acción.

---

## 🧩 Arquitectura del Workflow

```mermaid
flowchart TD
    A[👤 Usuario] --> B[🤖 AgenteClasificadorTipo]
    B --> C{SwitchNode(tipo_consulta)}
    C -->|tecnica| D1[🧰 AgenteDiagnostico]
    D1 --> D2[🔧 AgenteSolucion (usa una Tool)]
    C -->|rrhh| E[🧾 AgenteRRHH]
    C -->|otro| F[💬 NodoMensajeGenerico]
    D2 --> G[(📤 Output Final)]
    E --> G
    F --> G

🪄 Descripción de cada nodo
Nodo	Tipo	Descripción
AgenteClasificadorTipo	Agente	Recibe la consulta del usuario y, usando un modelo Pydantic, determina si la categoría es “técnica”, “rrhh” u “otro”.
SwitchNode	Nodo lógico	Ramifica el flujo según el valor de tipo_consulta.
AgenteDiagnostico	Agente	Analiza la descripción técnica del problema.
AgenteSolucion	Agente + Tool	Genera una respuesta o ejecuta una acción. Puede llamar una función externa como herramienta (ej. get_solution_info()).
AgenteRRHH	Agente	Atiende consultas del área de recursos humanos.
NodoMensajeGenerico	Nodo	Devuelve una respuesta estándar cuando no se reconoce el tipo de consulta.
🧠 Conceptos que se demuestran

Uso de workflow con branching logic (switch) para tomar decisiones dinámicas.

Implementación de un flujo secuencial dentro de una rama (dos agentes encadenados).

Ejemplo de integración de tool externa en el último agente.

Uso de modelos Pydantic para estructurar y validar datos entre agentes.


agent-framework-demo/
│
├── main.py
├── agents/
│   ├── classifier_agent.py
│   ├── diagnostic_agent.py
│   ├── solution_agent.py
│   └── hr_agent.py
│
├── tools/
│   └── solution_tool.py
│
├── models/
│   └── message_models.py
│
└── README.md