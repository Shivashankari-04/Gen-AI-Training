# LangGraph: Conditional Branching & Sentiment Analysis Architecture

```mermaid
graph TD
    classDef main fill:#2C3E50,stroke:#34495E,stroke-width:2px,color:#fff;
    classDef positive fill:#27AE60,stroke:#2ECC71,stroke-width:2px,color:#fff;
    classDef negative fill:#C0392B,stroke:#E74C3C,stroke-width:2px,color:#fff;
    classDef neutral fill:#BDC3C7,stroke:#95A5A6,stroke-width:2px,color:#2C3E50;
    classDef observe fill:#8E44AD,stroke:#9B59B6,stroke-width:2px,color:#fff;

    A[User Input via Streamlit UI]:::main --> B[Pandas Cleaning & Preprocessing]:::main
    B --> C[Sentiment Analysis Execution Node]:::main
    
    C -- "LangGraph Router Function extracts Status" --> D{"add_conditional_edges()"}:::observe
    
    D -.->|"> 0.1 Polarity"| E[handle_positive node]:::positive
    D -.->|"< -0.1 Polarity"| F[handle_negative node <br> Escalate Request]:::negative
    D -.->|"0.0 Polarity"| G[handle_neutral node]:::neutral
    
    E --> H[Format Output to the UI]:::main
    F --> H
    G --> H
```

### Overview of Dynamics

The **LangGraph Router** logic physically isolates your decision-making boundaries from your strict application boundaries. Because the edge layer determines routing strictly across pre-registered node labels (*e.g., `POSITIVE`, `NEGATIVE`*), your execution pipeline can dynamically fork without bloating a single file or standard Python namespace.
