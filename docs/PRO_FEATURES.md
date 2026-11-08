# clanki — Pro Specification & Feature Roadmap

This document outlines the complete architectural roadmap and CLI specification to elevate **clanki** from a minimalist terminal flashcard reviewer into an elite, fully featured terminal client for Anki power users (medical students, polyglots, competitive exam candidates, and software engineers).

---

## 1. Unified CLI Specification (`ank -h`)

Below is the complete reference design for the expanded CLI interface:

```text
clanki — The Elite Terminal Client for Anki

USAGE:
  ank [OPTIONS] [SUBCOMMAND]
  ank [DECK_NAME]                    # Shortcut: review a deck immediately

SUBCOMMANDS:
  review <deck>                      Launch an interactive review session for a deck
  add [deck]                         Create a new card/note in $EDITOR
  cram <query>                       Create a temporary filtered study session (e.g. tag:cram)
  search <query>                     Search collection with interactive table & batch actions
  note <note_id>                     Inspect and modify note type, fields, or deck
  sync                               Trigger bidirectional AnkiWeb synchronization
  stats [deck]                       Display visual terminal retention, heatmaps & due charts
  profile [name]                     List or switch Anki user profile
  daemon [start|stop|status]         Manage the background headless Anki instance

GLOBAL OPTIONS:
  -p, --profile <NAME>               Target a specific Anki profile
  -m, --model <NAME>                 Note type / model (for 'add' or 'note')
  --headless                         Force offscreen Qt mode (default when GUI is closed)
  --gui                              Require active Anki desktop GUI window
  --no-sound                         Mute audio auto-playback during reviews
  -v, --version                      Print version and build telemetry
  -h, --help                         Print this comprehensive help menu

INTERACTIVE REVIEW KEYBINDINGS:
  [Enter] / [Space]                  Reveal answer
  [1] Again  [2] Hard  [3] Good  [4] Easy   Grade card (shows scheduled intervals)
  [u]                                Undo last review action (grade, bury, edit)
  [e]                                Edit raw card fields in $EDITOR
  [m]                                Change note type / model mapping
  [t]                                Add, remove, or view card tags
  [f]                                Cycle or set card flag (1:Red .. 7:Purple, 0:None)
  [!]                                Suspend / Unsuspend current card
  [-]                                Bury card (skip until tomorrow)
  [=]                                Bury entire note (skip sibling cards)
  [r]                                Replay card audio / media
  [i]                                Inspect card history (lapses, stability, difficulty, FSRS)
  [d]                                Move card / note to another deck
  [q]                                Return to deck selector or exit
```

---

## 2. Note & Card Lifecycle Architecture

### 2.1 Changing Note Type (Model Mapping)

Changing note types (e.g., converting a `Basic` card to `Cloze`, or `Basic (and reversed)` to a custom template like `AnKing`) is a critical power-user feature.

- **AnkiConnect Endpoint**: `modelNames`, `modelFieldNames`, and backend SQLite transaction mapping.
- **Workflow**:
  1. User triggers `[m]` during review or via `ank note <id> --change-type <new_model>`.
  2. The system prompts to select the target model from `modelNames`.
  3. Interactive field-mapping matrix:
     ```text
     [Target: Cloze]           <---  [Source: Basic]
     • Text                   <---  Front (Default)
     • Back Extra             <---  Back  (Default)
     • Notes                  <---  [Unmapped / Discard]
     ```
  4. Once confirmed, old field contents are mapped to the new schema and committed.

### 2.2 Tagging & Flagging

- **Flagging (`[f]`)**:
  - Direct AnkiConnect binding: `setCardFlag(cards=[cardId], flag=1..7)`.
  - Visual terminal indicators: Colored flag badges in the header:
    - `⚑ Red`, `⚑ Orange`, `⚑ Green`, `⚑ Blue`, `⚑ Pink`, `⚑ Turquoise`, `⚑ Purple`.
- **Tagging (`[t]`)**:
  - Direct AnkiConnect binding: `getNoteTags`, `addTags`, `removeTags`.
  - Terminal modal with autocomplete for existing collection tags.

### 2.3 Card State Operations

- **Suspend / Unsuspend (`[!]`)**:
  - `suspend(cards=[cardId])` / `unsuspend(cards=[cardId])`.
  - Instantly pulls the card out of the study queue and shows a dimmed status badge `[SUSPENDED]`.
- **Bury Card & Bury Note (`[-]`, `[=]`)**:
  - `buryCards(cards=[cardId])`: Skips card until the next day without affecting scheduling intervals.
  - Useful when reviewing related sibling cards in the same session.
- **Reset Card / Forget**:
  - `resetCards(cards=[cardId])`: Resets intervals to New status for relearning from scratch.

### 2.4 Quick Card Creation (`ank add [deck]`)

- Command: `ank add "CSCA::Physics" --model "Basic"`
- Workflow:
  1. Opens `$EDITOR` populated with a pre-filled template:
     ```text
     # === FIELD: Front ===
     What is Snell's Law?

     # === FIELD: Back ===
     n1 * sin(θ1) = n2 * sin(θ2)

     # === TAGS ===
     physics optics formula
     ```
  2. On save and exit, validates fields and calls `addNote(note={...})`.
  3. Displays confirmation with the generated `noteId`.

---

## 3. Review & Scheduling Engine (FSRS & SM-2)

### 3.1 Interval Previews on Rating Buttons

Power users need to see the exact resulting interval before pressing a grading key:

```text
Rating:  [1] Again (10m)   [2] Hard (1.2d)   [3] Good (3.5d)   [4] Easy (8.0d)
```

- **Source**: `guiCurrentCard` provides `nextReviews` (or calculation from FSRS/SM-2 parameters).
- Displays elapsed time format (`10m`, `1d`, `2.4mo`, `1.1y`).

### 3.2 Review Undo (`[u]`)

- Power users review at 200–400 cards/hour; misclicks are inevitable.
- **Mechanism**:
  - Call AnkiConnect `undo` immediately to roll back the scheduler state machine and restore the previous card to the screen.

### 3.3 Card Inspector (`[i]`)

- Pressing `[i]` displays a static overlay detailing:
  - **Scheduling Algorithm**: SM-2 vs. FSRS-5
  - **Stability & Difficulty**: (e.g. `Stability: 14.2d`, `Difficulty: 4.8 / 10`)
  - **Review History**: Total reviews, lapses count, retention rate, average answer time.
  - **Due Date**: Exact calendar date and relative days remaining.

### 3.4 Filtered / Cram Sessions (`ank cram <query>`)

- Creates a temporary filtered deck for targeted studying before exams:
  - Example: `ank cram "deck:CSCA is:due prop:reps>5"`
  - Example: `ank cram "tag:high-yield is:new"`
- Automatically returns cards to their original decks upon session completion.

---

## 4. Media & Audio Engine

### 4.1 Audio Auto-Playback & Replay (`[r]`)

- Flashcards with language pronunciation or audio clips include `[sound:filename.mp3]`.
- **Terminal Implementation**:
  - Query media file location using Anki's media directory.
  - Spawn a non-blocking background audio player using standard system binaries (`mpv --no-video`, `ffplay -nodisp -autoexit`, or `paplay`).
  - Pressing `[r]` triggers immediate replay.

### 4.2 Terminal Image Rendering

- For anatomy, geography, and diagram flashcards:
  - **Tier 1 (High-Res Inline)**: Sixel or Kitty Graphics Protocol (renders high-res images directly within Alacritty, Kitty, WezTerm, iTerm2).
  - **Tier 2 (ASCII/Block Fallback)**: `chafa` terminal art conversion for universal compatibility.
  - **Tier 3 (External Viewer)**: `[v]` launches lightweight image viewer (`feh`, `imv`) without interrupting review flow.

---

## 5. Search & Interactive Card Browser (`ank search`)

- Launching `ank search "is:due tag:optics"` opens a static terminal grid:

```text
╔════════════════════════════════════════════════════════════════════════════╗
║ ID       DECK               DUE        FLAGS    FRONT SNIPPET              ║
╠════════════════════════════════════════════════════════════════════════════╣
║ 10421    CSCA::Physics      Today      ⚑ Red    In Young's double-slit...  ║
║ 10422    CSCA::Physics      Tomorrow   —        Diffraction grating eq...  ║
║ 10589    Genesis Protocol   Overdue    ⚑ Blue   Byzantine fault thresh...  ║
╚════════════════════════════════════════════════════════════════════════════╝
[↑/↓] Navigate   [Space] Select   [!] Suspend   [-] Bury   [f] Flag   [e] Edit
```

---

## 6. Profiles & Sync Management

- **AnkiWeb Sync (`ank sync`)**:
  - Triggers `sync` via AnkiConnect.
  - Shows progress bar during media sync.
  - Optional flag: `ank --sync-on-exit`.
- **Multi-Profile Switching (`ank profile [name]`)**:
  - Queries `getProfiles` and switches active profile via `loadProfile`.

---

## 7. Implementation Roadmap & Priority Matrix

| Phase       | Feature Milestone                                             | Complexity | Impact   |
| :---------- | :------------------------------------------------------------ | :--------- | :------- |
| **Phase 1** | **Review Undo (`[u]`)**                                       | Low        | Critical |
| **Phase 1** | **Flagging (`[f]`) & Tagging (`[t]`)**                        | Low        | High     |
| **Phase 1** | **Card Actions: Suspend (`[!]`), Bury (`[-]`), Move (`[d]`)** | Low        | High     |
| **Phase 2** | **FSRS / SM-2 Next Review Interval Badges**                   | Medium     | High     |
| **Phase 2** | **Card Inspector (`[i]`) Overlay**                            | Medium     | Medium   |
| **Phase 2** | **Audio Playback (`[sound:...]` with `mpv`/`aplay`)**         | Medium     | High     |
| **Phase 3** | **Quick Card Creation (`ank add`) via `$EDITOR`**             | Medium     | High     |
| **Phase 3** | **Change Note Type / Model Matrix Mapper (`[m]`)**            | High       | Critical |
| **Phase 4** | **Interactive Terminal Browser (`ank search <query>`)**       | High       | High     |
| **Phase 4** | **Inline Graphics (Kitty / Sixel / Chafa)**                   | High       | Medium   |
