# HTML5 Frontier Demo

A self-contained, single-file HTML5 interactive demo showcasing modern web technologies.

## Project Overview

This is a comprehensive HTML5 demo that includes:
- Interactive UI with dark/light theme toggle
- Canvas-based particle system and drawing tools
- Audio synthesis and visualization
- CSS animation and transformation demonstrations
- Browser intelligence dashboard
- AI chat interface with Cerebras Cloud integration

## Getting Started

### Prerequisites

No build tools or dependencies required. This is a standalone HTML file.

### Running the Project

1. Open `index.html` directly in any modern web browser
2. No server, build, or installation steps needed

## Project Structure

```
index.html            # Single file containing all HTML, CSS, and JavaScript
CLAUDE.md             # Guidance for AI code assistants
README.md             # Project documentation (this file)
mempalace.yaml        # Memory palace configuration for context management
swa-cli.config.json   # Static Web Apps CLI configuration
.env                  # Environment variables
```

## Key Features

### Browser Intelligence
- Real-time system monitoring (FPS, network, viewport, etc.)
- Device and browser capability detection
- User agent analysis

### Canvas Laboratory
- Particle system with configurable gravity, count, and hue shifting
- Drawing board with multiple tools (pen, line, circle, rectangle, eraser)
- Fractal viewer with zoom and color scheme options

### Audio Laboratory
- Web Audio API synthesizer with waveform selection
- ADSR envelope controls
- Real-time audio visualization
- Piano keyboard interface

### CSS Showcase
- 15+ CSS animations (spin, pulse, bounce, shake, wave, flip 3D, morph, float, etc.)
- 3D transforms with perspective controls
- CSS filters (blur, grayscale, sepia, hue-rotate, etc.)
- Gradient and color demonstrations
- Typography effects (gradient text, neon glow, outlined text)
- Clip-path shapes and mix blend modes

### API Demos
- Cerebras AI chat integration
- Local storage for API key persistence
- JSON export functionality

## Development Workflow

Since this is a single-file project, development involves:
1. Editing `index.html` directly
2. Refreshing the browser to see changes
3. Using browser developer tools for debugging

## Best Practices for Future Reference

### For Developers
- All code is contained in `index.html` - look for HTML, CSS, and JavaScript sections
- CSS custom properties (variables) are defined in `:root` for theme management
- The dark/light theme toggle is implemented via the `data-theme` attribute
- Event listeners are attached using standard DOM methods

### For AI Assistants
- Refer to `CLAUDE.md` for specific guidance
- The `mempalace.yaml` file configures memory context for AI interactions
- This `README.md` provides project overview and structure

## Configuration Files

### mempalace.yaml
Configures memory palace "rooms" for organizing context:
- `www`: Files from www/ directory
- `general`: Files that don't fit other categories

### swa-cli.config.json
Configuration for Azure Static Web Apps CLI.

### .env
Environment variables for the application.

## Contributing

Since this is a self-contained demo, contributions should maintain the single-file structure unless explicitly discussed.

## License

[Specify license here]