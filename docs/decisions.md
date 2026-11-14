# Decisions

Short notes for choices that are easy to re-litigate. The reasons live in the specs and
the constitution; this page is the index.

## Profiles are directories

A profile is `profile/<slug>/master.json` plus an optional `blocklist.txt`. The slug is the
identity and the display name, and profiles are listed in order. One source of truth per
name.

## Runs do not snapshot the profile

A run stores its digest, selection, artifacts, and the profile slug. It does not copy the
master. Re-rendering uses the current profile and fails validation when a selected id no
longer exists. The PDF on disk remains the record of what was produced.

## The corpus is append-only

Every successful analyze appends one record to `data/corpus.jsonl`, keyed by the hash of
the normalized posting. It never stores the posting text. Deleting runs does not delete
the market history.

## Models are usable before they are admitted

An unevaluated model runs marked `model_unadmitted` in the report, the CLI, and settings.
Admission is a separate, explicit act that records the evaluation. It never edits the
chain configuration.

## The service lives at the package root

`service.py` and `pipeline.py` sit above the layers. The core stays pure; the adapters stay
thin. There is no seventh layer.

## Translations are reviewed with their source

A master item is bilingual. One variant is verified by quote; the other is translated from
it, carries the source text, and is approved in the same decision. Nothing is translated
during tailoring or rendering.

## CrewAI stays out

The version 1 pipeline is a fixed sequence of validated steps behind `AgentStep`. An agent
framework would hide retries and validation. Reconsidering it needs an amendment and an
evaluation against the plain implementation.
