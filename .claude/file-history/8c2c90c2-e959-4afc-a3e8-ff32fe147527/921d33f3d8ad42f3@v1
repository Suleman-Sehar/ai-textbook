# Quickstart Guide: Physical AI & Humanoid Robotics Textbook

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- Git for version control
- Ubuntu 22.04 (for running validation scripts)

## Setup

1. **Install Docusaurus globally**:
   ```bash
   npm install -g @docusaurus/core@latest
   ```

2. **Initialize the textbook project**:
   ```bash
   npx create-docusaurus@latest textbook-physical-ai classic
   cd textbook-physical-ai
   ```

3. **Install required dependencies**:
   ```bash
   npm install
   ```

## Project Structure

The textbook follows this organization:

```
docs/                   # All textbook chapters
├── module-1-ros2/      # ROS 2 Nervous System content (Weeks 1-5)
├── module-2-digital-twin/  # Digital Twin content (Weeks 6-7)
├── module-3-nvidia-isaac/  # NVIDIA Isaac AI Brain content (Weeks 8-10)
└── module-4-vision-language-action/  # Vision-Language-Action content (Weeks 11-13)
diagrams/               # 12 diagrams (SVG/PNG)
code/                   # 20 runnable examples
scripts/                # CI scripts
templates/              # frontmatter + content templates
```

## Creating Content

1. **Add a new module**:
   ```bash
   mkdir docs/module-5-example
   ```

2. **Create a content file with proper frontmatter**:
   ```markdown
   ---
   id: introduction
   title: Introduction to Example Module
   sidebar_label: Introduction
   ---

   # Introduction to Example Module

   This module covers the basics of ...
   ```

3. **Add code examples to the `code/` directory** following the same module structure

4. **Add diagrams to the `diagrams/` directory** following the same module structure

## Validation

Run validation checks to ensure content meets requirements:

```bash
# Check word count
python scripts/check-wordcount.py

# Check links
bash scripts/link-check.sh

# Run all validation
bash scripts/verify.sh
```

## Building and Serving

1. **Build the textbook**:
   ```bash
   npm run build
   ```

2. **Serve locally for preview**:
   ```bash
   npm run serve
   # or for development:
   npm start
   ```

## Deployment

Deploy to Vercel using the command line or Vercel dashboard:

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

## Templates

Use the provided templates in the `templates/` directory to ensure consistent formatting:

- `module-template.md`: Template for new modules
- `frontmatter-template.yaml`: Standard frontmatter structure