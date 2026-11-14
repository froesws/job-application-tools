# Phase 0 Research: Frontend

## 1. Client generation

**Decision**: `openapi-typescript` generates `src/api/schema.d.ts` from
`backend/openapi.json`; a thin `client.ts` wraps `fetch` and is the only place HTTP
appears.

**Rationale**: the constitution requires a generated client, and the schema is already
checked in with a drift gate. Types alone are enough: a wrapper of about a hundred lines
is more readable than a generated SDK, and it keeps error handling in one place.

**Alternatives considered**: `orval` (generates hooks too, but adds a second source of
truth for query keys and a large generator); hand-written types (drift).

## 2. Query keys and invalidation

**Decision**: one `keys.ts` exports every query key. Mutations invalidate the keys they
affect explicitly; the render-only edit invalidates the derived run and the history, never
the analysis.

**Rationale**: stale UI is the failure mode of this app, and scattered keys make it
invisible. One module makes the invalidation graph reviewable and testable.

**Alternatives considered**: keys inline in each hook (invisible cross-screen effects);
global invalidation on every mutation (refetches the analysis after every edit).

## 3. Profile selection in the URL

**Decision**: the selected profile is a search parameter on every route; the selector
writes it and each screen reads it. A missing parameter falls back to the first profile
in slug order.

**Rationale**: the spec requires a refresh to keep the profile, and a URL parameter makes
deep links and back/forward work without extra state.

**Alternatives considered**: React context only (lost on refresh); localStorage (two
sources of truth with the URL).

## 4. Errors

**Decision**: the client normalizes every failure to `{code, message}`. Screens render the
message and keep the code visible in a subdued line. Unknown codes fall back to a generic
message plus the code.

**Rationale**: the backend already guarantees the shape, and the code is what makes a bug
report precise. Hiding it loses the only stable identifier.

**Alternatives considered**: toast-only errors (disappear before they are read); stack
traces in the UI (noise, and leaks internals).

## 5. Screen states

**Decision**: one `ScreenState` component renders loading, empty, and error. Each loading
state names what is loading.

**Rationale**: the spec forbids a bare spinner, and a shared component prevents five
different patterns.

**Alternatives considered**: per-screen ad hoc markup (divergence); a skeleton library
(new dependency).

## 6. The posting after submission

**Decision**: the posting text lives in component state only and is cleared on a
successful tailor response. It is never written to storage or to the URL.

**Rationale**: the constitution forbids exposing the posting, and the backend's response
never returns it. Clearing on success keeps it out of the browser history and the cache.

**Alternatives considered**: keeping it for a retry (leaves private text on screen);
persisting to localStorage (durable leak).

## 7. PDF preview

**Decision**: the preview requests the artifact endpoint as a blob and renders it in an
`iframe` with the browser's PDF viewer; the download uses the same endpoint.

**Rationale**: the browser already renders PDFs, and the app must show the exact artifact,
not a reconstruction.

**Alternatives considered**: pdf.js (a large dependency for a viewer the browser has);
an image thumbnail (does not prove pagination).

## 8. Testing

**Decision**: Vitest with Testing Library and `user-event`. Each test mocks the generated
client module; the viewmodels are exercised through the component, not in isolation.

**Rationale**: domain rules are already covered at the API seam. Mocking at the client
boundary keeps the tests about what the user sees, with no network and no new dependency.

**Alternatives considered**: MSW (a dependency and a second routing layer); testing the
hooks directly (asserts implementation, not behaviour).

## 9. Accessibility baseline

**Decision**: labelled inputs, visible focus, keyboard-reachable actions, one `h1` per
screen, and no colour-only state. Reviewed with a keyboard-only pass in F7.

**Rationale**: the app is used daily by one person with a keyboard, and the cost is small
at build time and large to retrofit.

**Alternatives considered**: an audit-only approach later (retrofit cost); a third-party
component kit (banned by the rules).

## 10. Gates

**Decision**: `tsc --noEmit`, `vitest run`, and `vite build` are Makefile targets that
join `check` and CI.

**Rationale**: the constitution requires frontend tests and build before merge, and the
backend already runs from `make check`.

**Alternatives considered**: a separate frontend CI job (two gates to keep in sync);
running only tests (a type error reaches the build).

## 11. Routing

**Decision**: React Router with plain routes and `BrowserRouter`; no data-router loaders.

**Rationale**: server state is TanStack Query's job; adding loaders would create a second
data path for the same screens.

**Alternatives considered**: data routers (duplicate data fetching); hash routing (ugly
URLs for no gain in a local app).

## 12. Rules conflict

**Decision**: `.opencode/rules/rules.md` is amended in the same change as F7 to permit
TanStack Query and React Router, and to record the frontend gates.

**Rationale**: the constitution mandates both libraries and supersedes the rules; leaving
the conflict in place means every session re-litigates it.

**Alternatives considered**: changing the constitution instead (it is the higher document
and its stack is deliberate).
