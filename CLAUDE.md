# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A self-contained, single-file HTML5 interactive demo (`index.html`). No build tools, dependencies, or configuration files — open directly in a browser.

## Documentation

- `README.md`: Comprehensive project documentation including structure, features, and development workflow
- `CLAUDE.md`: Guidance specifically for AI code assistants
- `mempalace.yaml`: Memory palace configuration for context management

## Running the Project

Open `index.html` directly in a web browser. No build, install, or server step required.

## Architecture

Everything lives in `index.html` as a single file with embedded HTML, CSS, and JavaScript:

- **HTML/CSS**: Dark-themed UI with gradient title, navigation tabs, and interactive elements
- **Interactive Features**:
  - Particle system with gravity, velocity, rotation, and alpha fade-out
  - Canvas drawing tools and fractal viewer
  - Web Audio API synthesizer and visualizer
  - CSS animation and transformation demonstrations
  - AI chat interface with Cerebras Cloud integration
- **Event handling**: Comprehensive event system for UI interactions, theme toggling, and real-time updates

## Configuration Files

- `mempalace.yaml`: Defines memory palace "rooms" for organizing context (www, general)
- `swa-cli.config.json`: Azure Static Web Apps CLI configuration
- `.env`: Environment variables

## Development Context

This project uses a single-file architecture for simplicity. All development occurs within `index.html`. The mempalace.yaml file suggests the use of a memory palace technique for context management, indicating this project values cognitive organization for better recall and understanding.
