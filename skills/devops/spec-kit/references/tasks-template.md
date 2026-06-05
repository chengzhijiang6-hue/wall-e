---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools
- [ ] T004 [P] Set up testing framework
- [ ] T005 [P] Configure CI/CD pipeline (if applicable)

---

## Phase 2: User Story 1 (P1)

**Goal**: Implement the highest priority user story

**Independent Test**: [How to test this story independently]

### Implementation

- [ ] T006 [US1] Create data model for [entity]
- [ ] T007 [US1] Implement core business logic
- [ ] T008 [P] [US1] Create API endpoint for [functionality]
- [ ] T009 [P] [US1] Implement frontend component for [feature]
- [ ] T010 [US1] Integrate components

### Testing

- [ ] T011 [P] [US1] Write unit tests for [component]
- [ ] T012 [US1] Write integration tests for [workflow]
- [ ] T013 [US1] Verify acceptance scenarios

---

## Phase 3: User Story 2 (P2)

**Goal**: Implement the second priority user story

**Independent Test**: [How to test this story independently]

### Implementation

- [ ] T014 [US2] [Implementation task]
- [ ] T015 [P] [US2] [Parallel implementation task]
- [ ] T016 [US2] [Integration task]

### Testing

- [ ] T017 [P] [US2] [Unit test task]
- [ ] T018 [US2] [Integration test task]
- [ ] T019 [US2] Verify acceptance scenarios

---

## Phase 4: User Story 3 (P3)

**Goal**: Implement the third priority user story

**Independent Test**: [How to test this story independently]

### Implementation

- [ ] T020 [US3] [Implementation task]
- [ ] T021 [US3] [Integration task]

### Testing

- [ ] T022 [US3] [Test task]
- [ ] T023 [US3] Verify acceptance scenarios

---

## Phase 5: Polish & Cross-Cutting Concerns

**Goal**: Final integration, optimization, and documentation

- [ ] T024 Cross-story integration testing
- [ ] T025 [P] Performance optimization
- [ ] T026 [P] Security review
- [ ] T027 [P] Update documentation
- [ ] T028 Final acceptance testing

---

## Dependencies Graph

```
T001 → T002 → T006 → T007 → T010
              ↓
T003 (parallel) → T011
T004 (parallel) → T012
T005 (parallel)

T014 → T016 → T018
T015 (parallel) → T017

T020 → T022
T021 → T023

T010 + T016 + T021 → T024 → T025 → T026 → T027 → T028
```

## Notes

- Tasks marked with [P] can be executed in parallel
- Each user story should be independently deployable
- Verify acceptance scenarios after completing each story
- Update this file as tasks are completed
