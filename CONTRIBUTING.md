# Development Setup

## Initial Setup

After cloning the repository, run:

```bash
# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (IMPORTANT!)
pre-commit install
```

## Pre-commit Hooks

This project uses pre-commit hooks to automatically:
- **Strip notebook outputs** before committing (prevents leaking account info)

The hooks run automatically on every `git commit`. If you need to run them manually:

```bash
# Run on all files
pre-commit run --all-files

# Run on specific file
pre-commit run --files notebooks/example.ipynb
```

## Working with Notebooks

**IMPORTANT**: Never commit notebooks with outputs that contain:
- Account IDs
- API tokens
- Balance information
- Personal data

The pre-commit hook automatically strips outputs, but if you need to do it manually:

```bash
jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
```

## Configuration

1. Copy the example config:
   ```bash
   cp config/oanda_config.ini.example config/oanda_config.ini
   ```

2. Add your credentials to `config/oanda_config.ini` (this file is gitignored)

3. Never commit `config/oanda_config.ini` - it contains sensitive data

## What's Ignored

The `.gitignore` protects:
- `*.ini` files (except `.example` files)
- `.env*` files (except `.example` files)
- `*.key`, `*.pem` (certificate files)
- `*.log` files
- `data/` directory (uncomment in `.gitignore` if needed)

## Testing Pre-commit

To verify the pre-commit setup works:

```bash
# This should strip outputs automatically
git add notebooks/01_retrieve_historical_data.ipynb
git commit -m "test commit"
```

If you see "Strip notebook outputs...Passed", it's working correctly!
