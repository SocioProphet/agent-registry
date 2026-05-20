# Noetica Agent Stub

This directory registers Noetica as a registry-visible surface agent for the SocioProphet / SourceOS stack.

Status: `registry-stub`.

This is not a production admission. It does not grant live provider access, does not store credentials, and does not admit sessions, memories, or runtime tool grants.

## Authority

- Authority repository: `SocioProphet/Noetica`
- Registry authority: `SocioProphet/agent-registry`
- Route evidence authority: `SocioProphet/agentplane`

## Required future grants

The manifest declares future grant dependencies only:

- `call:anthropic`
- `call:openai`
- `call:neuronpedia:steer`

Each grant is marked `not-admitted`. Production SourceOS mode must resolve grants through agent-registry before Noetica may use them as governed runtime authority.

## Boundary

Standalone Noetica may use runtime environment variables outside the registry. SourceOS mode must migrate provider access to governed grant resolution. This directory makes that future boundary explicit without pretending the grant already exists.
