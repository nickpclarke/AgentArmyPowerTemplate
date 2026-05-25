---
tags: [moc, board, platform]
track: board
---
# 🎛 Obsidian Board (AgentArmy Labs)

> [!tip] Welcome to the fun control panel
> Use this page when you want fast navigation and “what should I read next?” energy.
> If you want the classic map, go to [[Welcome]]. If you want the cross-layer map, go to [[Platform Atlas]].

**🏠 [[Welcome]] · 🧭 [[Platform Atlas]] · 🧪 [[Model-Driven Platform]] · 🧱 [[Middle-Core]] · 🏷️ [[Taxonomy]]**

## 🎲 Choose a track

| Track | When you're trying to… | Start |
|---|---|---|
| **Vision** | clarify the bet; align on “one model, many projections” | [[Model-Driven Platform]] |
| **Middle-Core** | reason about business objects + scenarios + evidence | [[Middle-Core]] |
| **Platform layers** | design a platform that builds platforms (all layers) | [[Platform Atlas]] |
| **Data + DB science** | make data + storage auditable, measurable, and evolvable | [[Data & Database Science Track]] |
| **OOP patterns** | keep the object model from melting under agentic change | [[OOP Patterns for Agentic Platforms]] |

## 🧭 Visual map

- Open `AgentArmy Labs Atlas.canvas` for a click-around diagram of the vault.

## 📚 Dashboards (Bases)

> [!info] What these are
> Bases are “live views” over notes using tags + properties. They’re the closest thing to a board without leaving Obsidian.

### Atlas (everything in one table)
![[Labs Atlas.base]]

### Vision
![[Vision.base]]

### Middle-Core (business objects)
![[Middle-Core.base]]

### Platform layers + primitives
![[Platform.base]]

### Data & database science
![[Data.base]]

### OOP patterns
![[OOP.base]]

### Open questions (things to revisit)
![[Open Questions.base]]

## 🧩 How to add a new note (so it shows up on the board)

1. Put it in this vault (folder doesn’t matter; tags do).
2. Add frontmatter with at least `tags:` and (ideally) `track:`.
3. Link it to at least one hub note so it’s reachable.

Template:
```yaml
---
tags: [platform] # or vision / middle-core / data / oop
track: platform  # optional but helps Bases group notes
---
```

> [!quote] Vault rule of thumb
> If it matters, it should be navigable from a hub, visible in a Base, and explainable in one screen.
