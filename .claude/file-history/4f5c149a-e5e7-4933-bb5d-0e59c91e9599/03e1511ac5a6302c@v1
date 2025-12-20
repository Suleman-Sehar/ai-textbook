# Deployment Guide

## Vercel Deployment

This Docusaurus textbook is configured for deployment on Vercel. The deployment process is automated with the following configuration:

### Configuration (vercel.json)
```json
{
  "rootDirectory": ".",
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "installCommand": "npm install",
  "framework": "docusaurus"
}
```

### Deployment Steps

1. **Connect to Vercel**:
   - Sign in to your Vercel account
   - Import the GitHub repository
   - Vercel will automatically detect the Docusaurus configuration

2. **Environment Variables** (if needed):
   - No special environment variables are required for this static site
   - The site will build using the default configuration

3. **Build Process**:
   - Vercel runs `npm install` to install dependencies
   - Then runs `npm run build` to generate the static site
   - Output is placed in the `build/` directory

4. **Preview & Production**:
   - Pull requests will generate preview deployments
   - Merges to main branch will trigger production deployment

## Alternative Deployment Options

### GitHub Pages
To deploy to GitHub Pages:

1. Update `docusaurus.config.js` with your GitHub repository details:
   ```javascript
   // GitHub pages deployment config.
   organizationName: 'your-username', // Usually your GitHub org/user name.
   projectName: 'your-repo-name', // Usually your repo name.
   baseUrl: '/your-repo-name/', // For GitHub pages subdomains
   ```

2. Run: `npm run deploy`

### Manual Deployment
1. Build the site: `npm run build`
2. The `build/` directory contains the complete static site
3. Deploy the contents to any static hosting service

## Post-Deployment Verification

After deployment, verify:

1. **Site Accessibility**: Ensure the site loads at the expected URL
2. **Navigation**: Test all module links and navigation
3. **Content**: Verify all content displays correctly
4. **Mobile Responsiveness**: Test on different screen sizes
5. **External Links**: Verify all external links are functional

## Troubleshooting

### Build Issues
- If builds fail, check the build logs for specific error messages
- Ensure all dependencies are properly configured in `package.json`
- Verify there are no syntax errors in configuration files

### Content Issues
- If content doesn't appear, verify the sidebar configuration in `sidebars.js`
- Check that all Markdown files have proper frontmatter
- Ensure file paths in links are correct

### Performance
- The site should load quickly due to Docusaurus optimizations
- If performance is slow, check for large images or heavy assets

## GitHub Repository Structure

The repository is organized as follows:
- `docs/` - All textbook content organized by module
- `diagrams/` - Visual diagrams and illustrations
- `code/` - Example code and conceptual examples
- `src/` - Docusaurus source files and components
- `scripts/` - Validation and utility scripts
- `specs/` - Project specifications and plans

## Continuous Integration

The project includes validation scripts that should be run before deployment:
- `npm run validate` - Check code quality and linting
- `scripts/check-wordcount.py` - Verify word count requirements
- `scripts/link-check.sh` - Check all internal links
- `scripts/verify.sh` - Run comprehensive validation

## Rollback Procedure

In case of deployment issues:
1. Identify the problematic commit in GitHub
2. Deploy a previous stable version from GitHub commits
3. Or revert the problematic changes and redeploy

## GitHub Repo Link
https://github.com/ai-textbook/physical-ai-textbook

## Vercel Deployment Link
https://physical-ai-textbook.vercel.app

## Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>