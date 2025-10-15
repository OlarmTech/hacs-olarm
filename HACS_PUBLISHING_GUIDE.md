# HACS Publishing Guide for Olarm Integration

This guide will walk you through publishing your Olarm integration to HACS (Home Assistant Community Store).

## Prerequisites

- ✅ GitHub repository set up (current repo: https://github.com/olarmtech/hacs-olarm)
- ✅ Integration code in `custom_components/olarm/`
- ✅ Required files created (hacs.json, README.md, LICENSE)

## Step 1: Push Your Code to GitHub

First, commit and push all your files:

```bash
cd /Users/pelicarno/Olarm/hacs-olarm
git add .
git commit -m "Initial HACS setup for Olarm integration"
git push origin main
```

## Step 2: Create a Release

HACS requires at least one release to work properly:

1. Go to your GitHub repository: https://github.com/olarmtech/hacs-olarm
2. Click on "Releases" (right sidebar)
3. Click "Create a new release"
4. **Tag version**: `v1.0.0` (must start with 'v')
5. **Release title**: `v1.0.0 - Initial Release`
6. **Description**: 
   ```
   Initial HACS release of the Olarm integration for Home Assistant.
   
   Features:
   - OAuth2 authentication
   - Real-time MQTT updates
   - Binary sensors for zones and system status
   - Full config flow support
   ```
7. Click "Publish release"

## Step 3: Validate Your Repository

Before submitting to HACS, ensure your repository meets all requirements:

### Required Files ✅
- [x] `custom_components/olarm/manifest.json` - Integration metadata
- [x] `custom_components/olarm/__init__.py` - Main integration file
- [x] `hacs.json` - HACS configuration
- [x] `README.md` - User documentation
- [x] `LICENSE` - License file
- [x] `info.md` - HACS info page (optional but recommended)

### HACS.json Validation
Your `hacs.json` should contain:
```json
{
  "name": "Olarm",
  "content_in_root": false,
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

### Manifest.json Requirements
- [x] Domain matches directory name
- [x] Has version field
- [x] Has documentation URL
- [x] Has issue_tracker URL
- [x] Requirements are properly specified

## Step 4: Add to HACS (Two Options)

### Option A: Add as Custom Repository (Immediate - Users can install right away)

Users can add your integration immediately without waiting for official HACS approval:

**Instructions for users:**
1. In Home Assistant, go to HACS > Integrations
2. Click the three dots (⋮) in the top right corner
3. Select "Custom repositories"
4. Add repository URL: `https://github.com/olarmtech/hacs-olarm`
5. Category: "Integration"
6. Click "Add"
7. Find "Olarm" in the list and install

**Share these instructions with your users!**

### Option B: Submit to HACS Default Repository (Takes time - Official listing)

To get your integration listed in the official HACS default repository:

1. Go to https://github.com/hacs/default
2. Fork the repository
3. Edit `integration` file
4. Add your repository to the list alphabetically:
   ```
   olarmtech/hacs-olarm
   ```
5. Create a Pull Request with title: "Add olarmtech/hacs-olarm"
6. Wait for HACS team review (can take several weeks)

**Requirements for HACS Default:**
- Repository must be public
- Must have at least one release
- Must follow HACS quality checklist
- Active maintenance commitment

## Step 5: Promote Your Integration

Once published, let users know:

1. **Update your main README** with installation badges
2. **Post on Home Assistant Community Forum**: https://community.home-assistant.io/
3. **Share on Reddit**: r/homeassistant
4. **Update Olarm documentation** to mention Home Assistant integration

## Maintaining Your Integration

### Creating New Releases

When you update your integration:

1. Update the version in `manifest.json`
2. Commit your changes
3. Create a new GitHub release (e.g., `v1.1.0`)
4. Add release notes describing changes
5. HACS will automatically detect the new version

### Versioning Guidelines

Follow Semantic Versioning (SemVer):
- **Major** (v2.0.0): Breaking changes
- **Minor** (v1.1.0): New features, backward compatible
- **Patch** (v1.0.1): Bug fixes, backward compatible

## Troubleshooting

### Common Issues

**Issue**: HACS says "Repository structure invalid"
- **Fix**: Ensure `content_in_root` is set to `false` in `hacs.json`
- **Fix**: Verify `custom_components/olarm/` structure exists

**Issue**: Integration not showing up in HACS
- **Fix**: Make sure you have at least one GitHub release
- **Fix**: Check that release tag starts with 'v' (e.g., v1.0.0)

**Issue**: Users can't authenticate
- **Fix**: Ensure `application_credentials` OAuth2 setup is documented
- **Fix**: Verify OAuth2 credentials in `const.py` are correct

## Syncing with Home Assistant Core

Once your integration is merged into Home Assistant core:

1. Add a deprecation notice to your HACS README
2. Point users to migrate to the official integration
3. Continue maintaining HACS version for users on older HA versions (optional)
4. Consider archiving the HACS repo after several HA releases

## Questions?

Before submitting:
- Do you want to use a different GitHub organization/username?
- Is your repository URL `https://github.com/olarmtech/hacs-olarm`?
- Do you need help with the OAuth2 setup for end users?

## Next Steps

1. ✅ Code is scaffolded
2. ⏳ Push to GitHub
3. ⏳ Create first release (v1.0.0)
4. ⏳ Test as custom repository
5. ⏳ (Optional) Submit to HACS default

