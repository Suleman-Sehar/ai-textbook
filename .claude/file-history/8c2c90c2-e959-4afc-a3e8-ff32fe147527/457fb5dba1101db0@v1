# Data Model: Physical AI & Humanoid Robotics Textbook

## Textbook Module
**Description**: Represents one of the four main course modules (ROS 2 Nervous System, Digital Twin, NVIDIA Isaac AI Brain, Vision-Language-Action)

**Fields**:
- id: string (kebab-case identifier, e.g., "module-1-ros2")
- title: string (display title)
- weeks: number (duration in weeks)
- weekRange: string (e.g., "Weeks 1-5")
- wordCount: number (target word count)
- examplesCount: number (minimum 5 examples)
- diagramsCount: number (exactly 3 diagrams)
- contentFiles: array of ContentFile
- exampleFiles: array of ExampleFile
- diagramFiles: array of DiagramFile

**Validation rules**:
- id must be unique across all modules
- wordCount must be between 3500-5000 (to meet overall target)
- examplesCount must be >= 5
- diagramsCount must be >= 3

## Content File
**Description**: Docusaurus Markdown files containing educational content, code examples, and diagrams with proper frontmatter

**Fields**:
- path: string (relative path from docs/ directory)
- title: string (display title)
- frontmatter: object (Docusaurus frontmatter with id, title, sidebar_label)
- content: string (Markdown content)
- wordCount: number (actual word count)
- module: TextbookModule (reference to parent module)

**Validation rules**:
- path must be unique across all content files
- frontmatter must contain required Docusaurus fields
- wordCount must contribute to module target

## Example File
**Description**: Runnable code examples that demonstrate concepts taught in the textbook

**Fields**:
- path: string (relative path from code/ directory)
- title: string (display title)
- description: string (brief explanation of what the example demonstrates)
- language: string (programming language)
- code: string (the actual code content)
- module: TextbookModule (reference to parent module)
- relatedContent: array of ContentFile (content files that reference this example)

**Validation rules**:
- path must be unique across all example files
- language must be a supported language for syntax highlighting
- code must include proper comments and type hints

## Diagram File
**Description**: Visual diagrams that support the educational content

**Fields**:
- path: string (relative path from diagrams/ directory)
- title: string (display title)
- description: string (brief explanation of what the diagram illustrates)
- format: string (SVG, PNG, or other supported format)
- altText: string (accessibility alt text)
- module: TextbookModule (reference to parent module)
- relatedContent: array of ContentFile (content files that reference this diagram)

**Validation rules**:
- path must be unique across all diagram files
- altText must be provided for accessibility
- format must be supported by Docusaurus