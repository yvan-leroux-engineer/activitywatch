# TODO

This file tracks planned improvements and features for the ActivityWatch Docker deployment.

## High Priority

### Query Module

- [ ] Implement and integrate the query module functionality
- [ ] Ensure query service is fully operational in Docker environment
- [ ] Add query module documentation

### WebUI Activity View

- [ ] Fix broken activity view in the WebUI
- [ ] Investigate and resolve rendering issues
- [ ] Test activity view functionality end-to-end

## Medium Priority

### Token Management UI

- [ ] Add UI for generating API tokens from the WebUI
- [ ] Implement token creation interface
- [ ] Add token management (view, revoke, regenerate)
- [ ] Include token usage statistics and monitoring

### Client-Side Token Personalization

- [ ] Add ability to customize tokens from client side
- [ ] Implement token naming/description features
- [ ] Add token expiration configuration
- [ ] Support for token scopes/permissions

## Low Priority

### Database Optimization - QuestDB Testing

- [ ] Test QuestDB migration as alternative to TimescaleDB
- [ ] Replace SQLx with HTTP client for QuestDB compatibility
- [ ] Adapt schema (remove hypertables, use QuestDB partitioning)
- [ ] Update queries to work with QuestDB HTTP API
- [ ] Compare performance vs TimescaleDB OSS
- [ ] Evaluate ~850MB additional savings potential (238MB vs 1.09GB)

### WebUI Refactoring

- [ ] Refactor graphs visualization components
- [ ] Improve graph rendering performance
- [ ] Refactor labeling/categorization UI components
- [ ] Modernize UI components and styling
- [ ] Improve accessibility and user experience

---

## Notes

- Items are organized by priority
- Check off items as they are completed
- Add new items as needed
