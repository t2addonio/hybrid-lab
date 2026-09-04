# Specialist Catalog
**Research & Engineering Multi-Agent System**  
**Version:** 0.6.1 (live) + RF specialist  
**Date:** 2026-08-15  

All specialists are **pure text plugins**. They receive a task string, return markdown, and may emit markers (`RESEARCH_NOTE:`, `CHANGE_PROPOSAL:`). They never execute tools.

Coordinator owns all INVOKE / FINAL decisions and marker → ToolCall promotion.

See the live file in this repository for the full roster: researcher, experiment_critic, coder, architect, residual_stream, vibration, quantum_sim, rf.

This file is mirrored from the lab catalog. Full specialist entries, T³ mappings, status matrix, and the add-specialist procedure are in the committed catalog body below.
