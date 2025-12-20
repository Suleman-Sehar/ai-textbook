# ADR-0001: Docusaurus as Textbook Platform

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Accepted
- **Date:** 2025-12-20
- **Feature:** 001-ai-robotics-textbook
- **Context:** The Physical AI & Humanoid Robotics Textbook project requires a platform for delivering educational content in a structured, accessible format. The platform must support extensive Markdown content, provide good navigation for course modules, and enable easy content management for textbook authors.

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security?
     2) Alternatives: Multiple viable options considered with tradeoffs?
     3) Scope: Cross-cutting concern (not an isolated detail)?
     If any are false, prefer capturing as a PHR note instead of an ADR. -->

## Decision

- Framework: Docusaurus v3
- Content Format: Markdown/MDX with frontmatter
- Deployment: Static site generation (Vercel/GitHub Pages compatible)
- Styling: Custom CSS with Docusaurus theme
- Navigation: Sidebar-based module organization
- Search: Built-in Docusaurus search
- Code Highlighting: Prism.js

## Consequences

### Positive

- Excellent Markdown/MDX support with frontmatter for metadata
- Built-in documentation site features (search, versioning, sidebar navigation)
- Strong React component integration for custom functionality
- Static site generation for fast loading and good SEO
- Active community and extensive plugin ecosystem
- Built-in support for diagrams and code examples
- Version control friendly for collaborative content creation

### Negative

- Additional complexity compared to plain HTML/CSS
- Potential performance issues with very large documentation sites
- Learning curve for Docusaurus-specific features and configurations
- Dependency on Node.js ecosystem and build process
- Potential lock-in to Docusaurus-specific features
- Build times may increase significantly as content grows

## Alternatives Considered

Alternative Stack A: Static HTML/CSS/JS - Simpler but lacks documentation-specific features, search, and navigation capabilities needed for textbook structure.

Alternative Stack B: GitBook - Good for documentation but less flexible for custom components and styling requirements.

Alternative Stack C: Hugo with Docsy theme - Static site generator with good documentation features but steeper learning curve and less React component flexibility.

Alternative Stack D: Next.js with custom MDX solution - More flexible but requires building documentation features from scratch instead of leveraging Docusaurus' built-in functionality.

## References

- Feature Spec: /specs/001-ai-robotics-textbook/spec.md
- Implementation Plan: /specs/001-ai-robotics-textbook/plan.md
- Related ADRs: None
- Evaluator Evidence: /history/prompts/general/0001-run-npm-to-see-ui-of-textbook.general.prompt.md
