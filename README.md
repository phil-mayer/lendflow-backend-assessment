# Lendflow Backend Assessment

This repo contains my (Phil Mayer's) solution for Lendflow's backend skills assessment. Note that this is a Python solution.

## Requirements

- A version of Docker supporting the newer `docker compose` syntax. If your version of Docker only supports the legacy `docker-compose` syntax, you may need to upgrade. Tested on with Docker Desktop v4.39.0.
- (Optional) An editor or IDE capable of attaching to a Docker container, e.g. VS Code. Particularly useful if you want to run the application in debug mode, but also for full syntax highlighting, autocompletion, etc.

## Setup

The following steps detail how to start the application with Docker. To use the container for development, additional steps are listed in the first sub-section below.

1. Copy `.env.example` to `.env` and change the values, particularly the `DJANGO_SECRET_KEY`, `POSTGRES_*`, and `NYT_` entries.
2. Fetch and build the Docker images via `docker compose build`. While we could simply run `docker compose up` at this point, this allows us to run the database migrations before taking up the entire stack.
3. Run `docker compose run web bash -c "python manage.py migrate"` to temporarily start the database and migrate it.
4. Run `docker compose up` (optionally with the `-d` flag to detach) to start the application.
5. Run `docker compose exec -it web bash -c "python manage.py createsuperuser"` to create a user account for yourself. For technical discussion of the decision to use a superuser account, see the next section.

### Using the Application

Once the application is running, navigate to [http://localhost:8000/admin/login/](http://localhost:8000/admin/login/) and log in with your user account created in the last step. On successful login, a cookie will be set in the browser. API requests can now be made directly using the same session.

For ease of querying the API, a [Swagger UI](https://swagger.io/tools/swagger-ui/) integration is provided. Navigate to [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/) to view the endpoint documentation and fire off sample requests.

> 📘 Note: If the application had permissions, I would have recommended creating a second non-super user for testing. I chose not to implement fine-grained authorization due to time, but also because Django permissions are typically associated with models (i.e. Django "content-types"). In a regular CRUD use-case, Django permissions can be understood as actions on objects or collections of objects, e.g. "can list books". Since this application is just a proxy, I didn't see a need to create any models, hence permissions. There are workarounds, but they felt like overkill for this assignment.

### Development Setup (Optional)

By default, development dependencies such as `pytest` and `ruff` (a static code analysis tool) are not installed in the steps above. To install them, ensure the Compose stack is up, then run `docker compose exec -it web bash -c "uv sync --frozen"`.

If you are using Visual Studio Code, a Python interpreter must be selected in order for some features to work as expected, such as syntax highlighting, IntelliSense, and visual debugger support. VS Code has a known limitation, however, where editor windows which have opened a folder on the host machine cannot use a container's Python interpreter. Instead, developers must either:

1. (Recommended) Use the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension to attach to the container, then select the Python interpreter in `/app/.venv/bin`. The downside of this approach is that it requires a couple of extra steps. Container crashes may also bring down the editor window, but this could be mitigated in the future by tweaking the `command` argument in the `Dockerfile` or `compose.yaml`.
2. Install `uv` and Python 3.12 (e.g. via `uv python install 3.12`), then run `uv sync --frozen` on the host machine. This approach requires extra software to be installed on the host. The developer also has to remember to install dependencies twice (on the container and in the host).

In addition, it may be useful to run the Django application in debug mode to expose more information about errors. Consider setting `DJANGO_DEBUG` to `True` as needed.

## Commands

All operations except viewing application logs require the "Development Setup" to have been completed above.

| Operation             | Host Command                                               | Container Command  |
|-----------------------|------------------------------------------------------------|--------------------|
| View Application Logs | `docker compose logs -f web`                               | -                  |
| Lint                  | `docker compose exec -it web bash -c "uv run ruff check"`  | uv run ruff check  |
| Format Code           | `docker compose exec -it web bash -c "uv run ruff format"` | uv run ruff format |
| Run Tests             | `docker compose exec -it web bash -c "uv run pytest"`      | uv run pytest      |

## Technical Notes

- I implemented my solution in Python with Django, extended with the Django REST Framework. I aimed to use the framework as much as possible to reduce complexity.
- To demonstrate knowledge of Docker/Docker Compose, I chose to use PostgreSQL. Given that this application will never enter real usage, SQLite would have worked as well.
- For caching, I chose to add a Redis instance to the Docker Compose stack. As noted above, given that this application will likely only run locally, Django's in-memory cache would have also sufficed.
- I decided to add Swagger UI to improve usability and discoverability of the main endpoint.
- While testing out the application, you may notice that the endpoints end in a trailing slash (`/`) by default. I decided to keep this behavior because it's common practice/configuration for a Django application.
- Aside from the tooling present in this repo, another good addition would be `mypy` for optional type-checking.
- I had never previously used the `uv` package/project manager. I found it to be pretty straightforward and much faster than `pip`.
- Having previously used `flake8` and `isort` for static code analysis, I decided to try out `ruff`. It's a **much** faster CLI tool rewritten in Rust.
- I used Astral's [UV documentation for Docker integration](https://docs.astral.sh/uv/guides/integration/docker/) to add Docker support. I leaned heavily on their [sample repository](https://github.com/astral-sh/uv-docker-example/tree/main), tweaking only a few things in the `Dockerfile` and `compose.yaml`. I chose not to use the Compose watch configuration because it does not support two-way file synchronization, and I recommend using dev containers above.

## Resources Used

- [https://docs.astral.sh/uv/guides/integration/docker/](https://docs.astral.sh/uv/guides/integration/docker/)
- [https://blog.pecar.me/uv-with-django](https://blog.pecar.me/uv-with-django)
- [https://www.django-rest-framework.org/topics/documenting-your-api/](https://www.django-rest-framework.org/topics/documenting-your-api/)
