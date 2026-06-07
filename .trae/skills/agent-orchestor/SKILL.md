---
name: "agent-orchestor"
description: "Orchestrates video creation workflow by sequentially executing social-video-generator, seedance-video-director, and seedance2-camera-man. Invoke when user provides a brief to create a complete social media video with human-in-the-loop confirmation."
---

# Agent Orchestrator for Seedance 2.0 Video Creation

This skill orchestrates the end-to-end video creation workflow for Seedance 2.0, coordinating three core skills in sequence:

## Workflow Sequence

1. **social-video-generator**: Generates optimized short video content for TikTok/Reels/Shorts from user's brief
2. **seedance-video-director**: Creates and analyzes optimized sales video scripts/storyboards
3. **seedance2-camera-man**: Calls Seedance 2.0 API to generate the final video from prepared assets

## Human-in-the-Loop Feature

At any step if there is uncertainty about required inputs for any skill, the orchestrator will pause and confirm details with the user before proceeding. This ensures all parameters are correct before calling downstream skills.

## When to Invoke

- User provides a product brief and wants to create a complete social media sales video
- Need to automate the sequential execution of video creation pipeline
- Require validation checks between skill transitions to ensure data consistency
