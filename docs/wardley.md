# Wardley Mapping

Strategic mapping for understanding competitive landscapes and positioning.

## What is a Wardley Map?

A Wardley Map visualizes:
- **User needs** — The top-level goals users want
- **Value chain** — Components/capabilities required to meet needs
- **Evolution** — Where each component sits in its lifecycle
- **Doctrine** — Universal principles guiding decisions
- **Climate** — External forces shaping strategy

## The Evolution Axis

```
Genesis        Custom         Product        Commodity
(Novel)        (Bespoke)      (Packaged)     (Utility)
   |              |               |              |
   v              v               v              v
  Invent        Build          Consume        Integrate
  ```

**Genesis**: Completely new, uncertain
**Custom**: Tailored solutions, high value
**Product**: Standardized products
**Commodity**: Utility services (electricity, HTTP)

## Creating a Wardley Map

### 1. Define User Need
What does the user fundamentally want?

Example: "Share photos with friends"

### 2. Map Value Chain
What capabilities are needed?

```
User Need: Share Photos
    ├── Photo Capture
    ├── Upload
    ├── Storage
    ├── Delivery
    └── Social Discovery
```

### 3. Position on Evolution
Where is each capability in its evolution?

```
Photo Capture   → Commodity (camera is everywhere)
Upload          → Commodity (HTTP)
Storage         → Product (AWS S3, Google Cloud)
Delivery        → Commodity (CDN)
Social          → Custom (differentiator)
```

### 4. Assess Doctrine
What principles guide your decisions?

- Focus on user outcomes
- Know your users
- Understand competition
- Design for ubiquity

### 5. Identify Climate
What external factors matter?

- Regulations (privacy, data)
- Competition (TikTok, Instagram)
- Technology (ML for recommendations)

## Using /wardley Skill

In Claude Code:

```
/wardley social media platform
```

Returns:
- User need definition
- Value chain decomposition
- Evolution positioning
- Doctrine and climate analysis
- Strategic recommendations

## Related Docs

- **[Capability Maps](capability-maps.md)**
- **[Architecture Decisions](architecture-decisions.md)**
