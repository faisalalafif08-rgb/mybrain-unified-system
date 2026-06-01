# MYBRAIN UNIFIED SYSTEM — Foundation Architecture

## Official Root

```text
C:\mybrain-unified-system\unified_ai_system
```

## Purpose

This document defines the official architecture constitution for **mybrain-unified-system**.

The system is not only PDF, OCR, Chat, or Studio. It is a unified Knowledge / Media / Production Operating System built around:

- General Mind
- System Heart
- Data Warehouse
- Memory: Bronze / Silver / Gold
- Agents and Personas
- Specialized Systems
- Interfaces
- Repository
- Registry
- Reports and Monitoring

## Main Rule

No direct execution.

No raw file enters the General Mind directly.

No ZIP, Legacy script, large library, interface, or external source runs directly.

No Agent makes the final decision.

No Gold write happens without Decision Gate.

## Official Flow

```text
Gateway
↓
Heart
↓
Router
↓
Dispatcher
↓
Registry / Name Graph
↓
Systems / Brains / Agents
↓
Reports
↓
Decision Gate
↓
Memory / Repository / Registry
↓
Interface Output
```

## Official Structure

```text
unified_ai_system/
├── 00_system_core
├── 01_general_mind
├── 02_data_warehouse
├── 03_memory
├── 04_agents
├── 05_specialized_systems
├── 06_interfaces
├── 07_runtime
├── 08_repository
├── 09_registry
├── 10_adapters
├── 11_policies
├── 12_docs
└── 13_tools
```

## System Heart

The Heart is the runtime and monitoring center.

```text
heart/
├── kernel/
├── orchestrator/
├── router/
├── dispatcher/
├── event_bus/
├── queues/
├── workers/
├── monitoring/
├── recovery/
├── readiness_gate/
├── decision_gate/
└── runtime_state/
```

Responsibilities:

- Receive tasks
- Check readiness
- Register events
- Route tasks
- Dispatch work
- Monitor workers
- Receive results
- Pass reports to Decision Gate
- Write state, logs, and reports
- Return status to the interface

## General Mind

The General Mind is the top decision layer.

The five methodologies are not just dependencies of the General Mind; the General Mind is composed of them.

Official location:

```text
01_general_mind/methodology_council/
```

Methodology IDs:

```text
MTH-001
MTH-002
MTH-003
MTH-004
MTH-005
```

The final decision comes from:

```text
decision_fusion
```

Not from a single agent, interface, or isolated methodology.

## Gateways

Main gateways:

1. Interface Gateway
2. File Gateway

Before Interface Gateway:

```text
Interface Quick Intake / Fast Pre-Handler
```

Then:

```text
Interface Intake Handler / Interface Gatekeeper
```

The interface displays, controls, and receives input only. It does not approve knowledge, write Gold, or run systems directly.

## Data Warehouse

The Warehouse is not a persona and does not make final decisions.

Responsibilities:

- Intake
- Hash
- Type Detection
- Metadata
- Classification
- Engine Routing
- Extraction
- Cleanup
- Quality
- Review
- Chunking
- Embedding
- Memory Write
- Agent Feed
- Report

## Large Systems Policy

Any large system such as PDF/OCR, Fooocus, EasyOCR, MMPose, Cinema System, Audio System, Video System, Avatar System, ZIP, old project, interface, or script must not run directly.

Correct path:

```text
Input / ZIP / Project / Library / Script / Interface
↓
Warehouse Intake
↓
SHA256 / Fingerprint
↓
Type Detection
↓
Metadata
↓
Classification
↓
Safe Extract
↓
Manifest
↓
Capability Mapping
↓
Unitization
↓
Adapter Contract
↓
Worker / Station
↓
BrainReport
↓
Bronze
↓
Silver
↓
Decision Gate
↓
Gold
↓
General Mind
```

## Memory

```text
memory/
├── bronze/
├── silver/
└── gold/
```

- Bronze = raw indexed data
- Silver = cleaned and structured data
- Gold = approved final knowledge

Gold is written only after Decision Gate.

## Agents

Agents are not just chat interfaces.

Each agent can have:

- working_memory
- private_memory
- learning_unit
- discovery_reports
- local_agent_mind

Agents can learn locally, debate, propose, object, and report.

Agents cannot:

- Write Gold
- Modify General Mind directly
- Modify Registry directly
- Approve final knowledge
- Run large systems directly
- Bypass Warehouse Review
- Bypass Decision Gate

## Official Personas

Current personas:

- FNO
- Amal
- Maya
- Lara
- Rawan
- Dunia

Roles are flexible and assigned by task context, not permanently locked.

## Interfaces

Interfaces display and control only.

Examples:

```text
interfaces/
├── home_shell/
├── control_center/
├── cinema_interface/
├── operation_room/
├── avatar_room/
├── voice_room/
├── music_control/
├── newsroom_panel/
├── admin_panel/
├── agents_room/
└── intelligence_dashboard/
```

## Quran Policy

Quran data is sensitive.

Rules:

- No direct Gold for Quran.
- No correction by guessing.
- No approval from OCR directly.
- Quran text must pass through reference systems, Review, and Decision Gate.

Official path:

```text
quran_reference_system
↓
religious_reference_system
↓
Review
↓
Decision Gate
```

## Name Graph

Official registry file:

```text
09_registry/name_graph.json
```

The Name Graph links:

- names
- agents
- systems
- interfaces
- sources
- paths
- legacy projects
- production rooms
- capabilities

## Status

This document is the foundation architecture document for:

```text
faisalalafif08-rgb/mybrain-unified-system
```
