# Wardley Analysis

Run the full five-stage Wardley Mapping pipeline on a user need or strategic domain.

## Usage

```
/wardley [domain or user need]
```

Example:
```
/wardley our patient scheduling capability
/wardley API management platform strategy
/wardley build vs buy decision for identity management
```

## What This Does

Invokes the `wardley-strategist` agent to run the complete analytical pipeline:

1. **Value Chain** — decompose the user need into a dependency hierarchy with visibility and evolution assignments
2. **Wardley Map** — position components on evolution axis (Genesis → Custom → Product → Commodity), add movement vectors and build/buy recommendations. Output as OWM syntax for [create.wardleymaps.ai](https://create.wardleymaps.ai)
3. **Doctrine Assessment** — score organizational maturity against 40 Wardley doctrine principles across 4 phases
4. **Climatic Patterns** — analyze external forces acting on the landscape (32 patterns, Peace/War/Wonder cycle)
5. **Gameplay Selection** — recommend strategic plays from a library of 60+ options, scored against current map position

## Output

- OWM syntax for map rendering
- Build/Buy/Borrow recommendations per component
- Doctrine maturity heatmap with top 3 priority improvements
- Climatic forces with likelihood/impact scores
- Recommended strategic plays with sequencing rationale
- 3-5 sentence strategic narrative

## Context

Designed for US enterprise and federal contexts. No UK-specific framework dependencies.
Maps render at: https://create.wardleymaps.ai
