# Lendflow Backend Assessment

This repo contains my (Phil Mayer's) solution for Lendflow's backend skills assessment. Note that this is a Python Django solution. My strongest language is TypeScript, but I chose Python for this assignment following a discussion about an internal team's increased usage of Python.

I recommend running the application and making calls against its provided Swagger UI page (see the "Setup" and "Usage" sections). If you're short on time and familiar with Python and/or Django, check out the following files in particular:

- `config/urls.py`: Top-level route mapping. When running, the application exposes routes for an admin site (very similar to a Laravel), an OpenAPI schema, Swagger UI, and the actual application routes on `/api/v1/`.
- `core/services/nyt_api_service.py`: Contains the NYT API caller function.
- `core/views/nyt_best_sellers_view.py`: REST controller (i.e. view set) backing the main endpoint. The top section contains underscored "private" classes used for controller-specific input sanitization and output object mapping. The endpoint implementation can be found below annotations for Swagger UI and cache configuration.
- `core/tests.py`: Commented endpoint-level tests.

## Requirements

- A version of Docker supporting the newer `docker compose` syntax. If your version of Docker only supports the legacy `docker-compose` syntax, you may need to upgrade. Tested on with Docker Desktop v4.39.0.
- (Optional) An editor or IDE capable of attaching to a Docker container, e.g. VS Code.

## Setup

The following steps detail how to start the application with Docker. To use the container for development, additional steps are listed in the next sub-section.

1. Copy `.env.example` to `.env` and change the values, particularly the `DJANGO_SECRET_KEY`, `POSTGRES_*`, and `NYT_` entries.
2. Fetch and build the Docker images via `docker compose build`. While we could simply run `docker compose up` at this point, this allows us to run the database migrations before taking up the entire stack.
3. Run `docker compose run --rm web bash -c "python manage.py migrate"` to temporarily start the database and migrate it.
4. Run `docker compose up` (optionally with the `-d` flag to detach) to start the application.
5. Run `docker compose exec web bash -c "python manage.py createsuperuser"` to create a user account.

If you only want to make API calls, skip ahead to the "Usage" section.

### Development Setup (Optional)

To complete the setup with all tooling, the fastest method is to attach your editor window to the running container. For Visual Studio Code, I recommend the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension. After attaching, open a new terminal within the container and run:

```sh
uv sync --frozen
```

This will install the `pytest` and `ruff` (a static code analysis tool) dependencies. You can now run:

```sh
uv run ruff check # lint
uv run ruff format # format
uv run mypy # static type checking
uv run pytest # run test suite
```

All syntax highlighting and step-into functionality should work as expected. If not, open the VS Code Command Palette (Cmd-Shift-P), select "Python: Select Interpreter", and choose the interpreter within `.venv/bin`.

## Usage

Once the application is running, navigate to [http://localhost:8000/admin/login/](http://localhost:8000/admin/login/) and log in with your user account created in the last step. On successful login, a cookie will be set in the browser. API requests can now be made directly using the same session.

For ease of querying the API, a [Swagger UI](https://swagger.io/tools/swagger-ui/) integration is provided. Navigate to [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/) to view the endpoint documentation and fire off sample requests. To do so:

1. Click the "GET /api/v1/nyt-best-sellers/" accordion button.
2. Press the "Try it out" button.
3. Populate any combination of the **optional** `author`, `isbn[]`, `offset`, and `title` query parameters.
4. Click "Execute" to run the request.

Alternatively, direct calls against `http://localhost:8000/api/v1/nyt-best-sellers/` will also work as expected.

## Technical Notes

- I implemented my solution in Python with Django, extended with the Django REST Framework. I aimed to use the framework as much as possible to reduce complexity.
- To demonstrate knowledge of Docker/Docker Compose, I chose to use PostgreSQL. Given that this application will never enter real usage, SQLite would have worked as well.
- For caching, I chose to add a Redis instance to the Docker Compose stack. Similar to the note above on PostgreSQL, Django's in-memory cache would have also sufficed.
- I decided to add Swagger UI to improve usability and discoverability of the main endpoint.
- While testing out the application, you may notice that the endpoints end in a trailing slash (`/`) by default. I decided to keep this behavior because it's common practice/configuration for a Django application.
- I had never previously used the `uv` package/project manager. I found it to be pretty straightforward and much faster than `pip`.
- Having previously used `flake8` and `isort` for static code analysis, I decided to try out `ruff`. It's a **much** faster CLI tool rewritten in Rust.
- I used Astral's [UV documentation for Docker integration](https://docs.astral.sh/uv/guides/integration/docker/) to add Docker support. I leaned heavily on their [sample repository](https://github.com/astral-sh/uv-docker-example/tree/main), tweaking only a few things in the `Dockerfile` and `compose.yaml`. I chose not to use the Compose watch configuration because it does not support two-way file synchronization, and I recommend using dev containers above.

## Resources Used

- [https://docs.astral.sh/uv/guides/integration/docker/](https://docs.astral.sh/uv/guides/integration/docker/)
- [https://blog.pecar.me/uv-with-django](https://blog.pecar.me/uv-with-django)
- [https://www.django-rest-framework.org/topics/documenting-your-api/](https://www.django-rest-framework.org/topics/documenting-your-api/)
- [https://docs.djangoproject.com/en/5.1/](https://docs.djangoproject.com/en/5.1/)
