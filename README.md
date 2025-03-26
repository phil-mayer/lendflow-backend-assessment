# Lendflow Backend Assessment

This repo contains my (Phil Mayer's) solution for Lendflow's backend skills assessment.

## Setup

### Local Setup

- `uv` version 0.6.8 or greater. The application is likely to work on older versions as well.
- Python 3.12.x

### Docker

- There might be a required version of Docker Desktop/Compose for `watch`.

### Steps

1. Copy `.env.example` to `.env` and enter values for the required key-value pairs.

## Technical Notes

- I had never previously used the `uv` package/project manager. I found it to be pretty straightforward and wildly fast compared to `pip`.
- Having previously used `flake8` and `isort` for static code analysis, I decided to try out `ruff`.
