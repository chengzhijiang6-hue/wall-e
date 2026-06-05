# Hermes CLI Skins

Hermes CLI has a skin engine (`hermes_cli/skin_engine.py`) that controls all visual elements: banner colors, spinner animations, branding text, tool prefixes, and status bar colors.

## Built-in Skins (9)

| Name | Description | Style |
|------|-------------|-------|
| `default` | Classic Hermes gold/kawaii | Gold/amber, kawaii spinner |
| `ares` | War-god theme | Crimson/bronze, sword spinners, custom ASCII art |
| `mono` | Clean grayscale monochrome | Gray tones, minimal |
| `slate` | Cool blue developer-focused | Blue accents, dark background |
| `daylight` | Light theme for bright terminals | Dark text on light bg, blue accents |
| `warm-lightmode` | Warm brown/gold for light terminals | Brown/gold text on light bg |
| `poseidon` | Ocean-god theme | Deep blue/seafoam, trident spinners, custom ASCII art |
| `sisyphus` | Sisyphean austere grayscale | Gray tones, boulder spinners, custom ASCII art |
| `charizard` | Volcanic theme | Burnt orange/ember, fire spinners, custom ASCII art |

## Switching Skins

**CLI command** (in-session):
```
/skin <name>
```

**Config file** (persistent):
```yaml
display:
  skin: ares
```

## Creating Custom Skins

Drop a YAML file in `~/.hermes/skins/<name>.yaml`. All fields are optional — missing values inherit from `default`.

```yaml
name: mytheme
description: My custom skin

colors:
  banner_border: "#CD7F32"
  banner_title: "#FFD700"
  banner_accent: "#FFBF00"
  banner_dim: "#B8860B"
  banner_text: "#FFF8DC"
  ui_accent: "#FFBF00"
  ui_label: "#DAA520"
  ui_ok: "#4caf50"
  ui_error: "#ef5350"
  ui_warn: "#ffa726"
  prompt: "#FFF8DC"
  input_rule: "#CD7F32"
  response_border: "#FFD700"
  status_bar_bg: "#1a1a2e"
  status_bar_text: "#C0C0C0"
  status_bar_strong: "#FFD700"
  session_label: "#DAA520"
  session_border: "#8B8682"

spinner:
  waiting_faces: ["(⚔)", "(⛨)"]
  thinking_faces: ["(⌁)", "(<>)"]
  thinking_verbs: ["forging", "plotting"]
  wings: [["⟪⚔", "⚔⟫"], ["⟪▲", "▲⟫"]]

branding:
  agent_name: "My Agent"
  welcome: "Welcome!"
  goodbye: "Goodbye!"
  response_label: " My Agent "
  prompt_symbol: "❯"
  help_header: "Commands"

tool_prefix: "┊"

tool_emojis:
  terminal: "⚔"
  web_search: "🔮"

# Optional: custom ASCII art logos (Rich markup)
banner_logo: |
  [bold #FFD700]MY CUSTOM LOGO[/]
banner_hero: |
  [#FFD700]ASCII ART HERO[/]
```

## Skin YAML Schema — Color Keys

| Key | Purpose | Default |
|-----|---------|---------|
| `banner_border` | Panel border color | `#CD7F32` |
| `banner_title` | Panel title text | `#FFD700` |
| `banner_accent` | Section headers | `#FFBF00` |
| `banner_dim` | Dim/muted text | `#B8860B` |
| `banner_text` | Body text | `#FFF8DC` |
| `ui_accent` | General UI accent | `#FFBF00` |
| `ui_label` | UI labels | `#DAA520` |
| `ui_ok` | Success indicators | `#4caf50` |
| `ui_error` | Error indicators | `#ef5350` |
| `ui_warn` | Warning indicators | `#ffa726` |
| `prompt` | Prompt text color | `#FFF8DC` |
| `input_rule` | Input area horizontal rule | `#CD7F32` |
| `response_border` | Response box border (ANSI) | `#FFD700` |
| `status_bar_bg` | Status bar background | `#1a1a2e` |
| `status_bar_text` | Status bar default text | `#C0C0C0` |
| `status_bar_strong` | Status bar highlighted text | `#FFD700` |
| `status_bar_dim` | Status bar separators | `#8B8682` |
| `status_bar_good` | Healthy context usage | `#8FBC8F` |
| `status_bar_warn` | Warning context usage | `#FFD700` |
| `status_bar_bad` | High context usage | `#FF8C00` |
| `status_bar_critical` | Critical context usage | `#FF6B6B` |
| `session_label` | Session label color | `#DAA520` |
| `session_border` | Session ID dim color | `#8B8682` |
| `voice_status_bg` | TUI voice status background | `#1a1a2e` |
| `selection_bg` | TUI mouse-selection highlight | `#333355` |
| `completion_menu_bg` | Completion menu background | `#1a1a2e` |
| `completion_menu_current_bg` | Active completion row | `#333355` |
| `completion_menu_meta_bg` | Completion meta column | `#1a1a2e` |
| `completion_menu_meta_current_bg` | Active completion meta | `#333355` |

## Skin YAML Schema — Branding Keys

| Key | Purpose | Default |
|-----|---------|---------|
| `agent_name` | Banner title, status display | `Hermes Agent` |
| `welcome` | CLI startup message | `Welcome to Hermes Agent!...` |
| `goodbye` | Exit message | `Goodbye! ⚕` |
| `response_label` | Response box header | ` ⚕ Hermes ` |
| `prompt_symbol` | Input prompt symbol | `❯` |
| `help_header` | /help header text | `(^_^)? Available Commands` |

## Skin YAML Schema — Other

| Key | Purpose | Default |
|-----|---------|---------|
| `tool_prefix` | Character for tool output lines | `┊` |
| `tool_emojis` | Per-tool emoji overrides (dict) | `{}` |
| `banner_logo` | Rich-markup ASCII art logo | `""` |
| `banner_hero` | Rich-markup hero art | `""` |

## Pitfalls

- User skins in `~/.hermes/skins/` shadow built-in skins if they share the same name
- Skin changes via `/skin` apply immediately in TUI; config file changes require restart
- `banner_logo` and `banner_hero` use Rich markup syntax (e.g. `[bold #FFD700]text[/]`)
