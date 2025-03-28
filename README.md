# Lendflow Backend Assessment

This repo contains my (Phil Mayer's) solution for Lendflow's backend skills assessment.

## Requirements

- A version of Docker (e.g. Docker Desktop for Mac) supporting Compose >= 2.22.0, required for [Compose Develop](https://docs.docker.com/reference/compose-file/develop/). To check the Compose version, run `docker compose version`. If your system only supports the `docker-compose` syntax, you likely need to upgrade Docker.
- (Optional) An editor or IDE capable of attaching to a Docker container, e.g. VS Code. Particularly useful if you want to run the application in debug mode, but also for full syntax highlighting, autocompletion, etc.

## Setup

The following steps detail how to start the application with Docker. To use the container for development, additional steps are required -- see the next sub-section.

1. Copy `.env.example` to `.env` and change the values, particularly the `DJANGO_SECRET_KEY` and `POSTGRES_*` entries.
2. Fetch and build the Docker images via `docker compose build`. While we could simply run `docker compose up` at this point, this allows us to run the database migrations before taking the entire stack up.
3. Run `docker compose run web bash -c "python manage.py migrate"` to temporarily start the database and migrate it.
4. Run `docker compose up` (optionally with the `-d` flag to detach) to start the application.

### Development Setup (Optional)

By default, development dependencies such as `pytest` and `ruff` (a static code analysis tool) are not installed in the steps above. To install them, ensure the Compose stack is up, then run `docker compose exec -it web bash -c "uv sync --frozen"`.

If you are using Visual Studio Code, a Python interpreter must be selected in order for some features to work as expected, such as syntax highlighting, IntelliSense, and visual debugger support. VS Code has a known limitation, however, where editor windows which have opened a folder on the host machine cannot use a container's Python interpreter. Instead, developers must either:

1. (Recommended) Use the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension to attach to the container, then select the Python interpreter in `/app/.venv/bin`. The downside of this approach is that it requires a couple of extra steps. Container crashes may also bring down the editor window, but this could be mitigated in the future by tweaking the `command` argument in the `Dockerfile` or `compose.yaml`.
2. Install `uv` and Python 3.12 (e.g. via `uv python install 3.12`), then run `uv sync --frozen` on the host machine. This approach requires extra software to be installed on the host. The developer also has to remember to install dependencies twice (on the container and in the host).

In addition, it may be useful to run the Django application in debug mode to expose more information about errors. Consider setting `DJANGO_DEBUG` to `True` as needed.

## Commands

| Operation             | Host Command                                              | Container Command |
|-----------------------|-----------------------------------------------------------|-------------------|
| View Application Logs | `docker compose logs -f web`                              | -                 |
| Lint                  | `docker compose exec -it web bash -c "uv run ruff check"` | uv run ruff check |
| Run Tests             | TO DO                                                     | -                 |

## Technical Notes

- I had never previously used the `uv` package/project manager. I found it to be pretty straightforward and much faster than `pip`.
- Having previously used `flake8` and `isort` for static code analysis, I decided to try out `ruff`. Not bad!
- I used Astral's [UV documentation for Docker integration](https://docs.astral.sh/uv/guides/integration/docker/) to add Docker support. I leaned heavily on their [sample repository](https://github.com/astral-sh/uv-docker-example/tree/main), tweaking only a few things in the `Dockerfile` and `compose.yaml`. I chose not to use the Compose watch configuration because it does not support two-way file synchronization, and I recommend using dev containers above.

## Resources Used

- [https://docs.astral.sh/uv/guides/integration/docker/](https://docs.astral.sh/uv/guides/integration/docker/)
- [https://blog.pecar.me/uv-with-django](https://blog.pecar.me/uv-with-django)
