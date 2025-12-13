# Research: Physical AI & Humanoid Robotics Textbook

## Decision: Docusaurus Version
**Rationale**: Docusaurus v3 is the latest stable version and provides the best features for creating educational content with support for MDX, theming, and deployment options. It's specifically designed for documentation and textbook-style content.

**Alternatives considered**:
- Docusaurus v2: Older version with fewer features, would require upgrade later
- GitBook: Less flexible for custom content types and diagrams
- Custom React site: More complex to maintain, no built-in documentation features

## Decision: Deployment Platform
**Rationale**: Vercel is specified as mandatory in the implementation plan and provides excellent performance for static sites, seamless GitHub integration, and reliable global CDN delivery.

**Alternatives considered**:
- GitHub Pages: Explicitly not allowed per requirements
- Netlify: Good alternative but Vercel is specified as mandatory

## Decision: Content Structure
**Rationale**: Organizing content by modules (4 modules for 13 weeks) follows the educational progression and makes it easy for students to follow along. Each module gets its own directory for better organization.

**Alternatives considered**:
- Single flat structure: Would be harder to navigate for large textbook
- Week-by-week organization: Would create too many small sections

## Decision: Code Example Structure
**Rationale**: Placing code examples in module-specific directories keeps them organized and related to their corresponding content. This makes it easier for students to find relevant examples.

**Alternatives considered**:
- Single code directory: Would mix examples from different modules
- Example-by-example directories: Would create too many small directories

## Decision: Diagram Organization
**Rationale**: Grouping diagrams by module follows the same organizational principle as content and code examples, making it easy to find relevant visuals for each topic.

**Alternatives considered**:
- Single diagrams directory: Would require prefixes to identify module association
- Topic-based organization: Would duplicate the module structure conceptually

## Decision: Scripting Language for Validation
**Rationale**: Using Python for validation scripts (word count, link checking) provides good text processing capabilities and cross-platform compatibility. Bash for simple operations that don't require complex logic.

**Alternatives considered**:
- Node.js: Would add another dependency to validation process
- Pure Bash: Limited for complex text processing tasks