# tap-userflow

`tap-userflow` is a Singer tap for UserFlow.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.



## Installation

Install from PyPi:

```bash
pip install kingalban-tap-userflow
```

Install from GitHub:

```bash
pipx install git+https://github.com/kingalban/tap-userflow.git@main
```

## Configuration

### Accepted Config Options

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-userflow --about
```

### Example Config File

```json
{
  "auth_token": "<userflow-api-key>"
}
```


### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Source Authentication and Authorization

Userflow uses Bearer authentication. Follow their documentation [here](https://userflow.com/docs/api#authentication) to generate API keys.

## Usage

You can easily run `tap-userflow` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-userflow --version
tap-userflow --help
tap-userflow --config CONFIG --discover > ./catalog.json
```

### Usage Notes
Userflow may hard delete `content_sessions` which can result in a `state` which can't be automatically recovered.
Example situation:
1. A `content_session` is ingested and it's ID is recorded as the latest state for that partition. 
2. Later that `content_session` is deleted. 
3. When `tap-userflow` tries to request the next `content_session`s for that partition is will make a request to `https://api.userflow.com/content_versions?content_id=<content_id>?starting_after=<deleted_session_id>&...`
4. Userflow API will respond with `400 Client Error: Bad Request for path: /content_sessions (code=\'invalid_params\'` `starting_after: Content session with id \'139ba1bd-ffe4-433e-8004-1fcf7556b75e\' not found`

Automatically recovering from this situation safely is tricky, so manually editing the state is necessary. 
You can do this by either removing the relevant partition from the state (causing a complete re-sync of the partition),
or by changing the `replication_key_value` to an earlier known good `content_session` id.

**Note**: The deleted `content_session` will remain wherever you delivered it to (your analytics database). 
If you have GDPR concerns about this, you should also manually remove it.

## Developer Resources

Follow these instructions to contribute to this project.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tests` subfolder and
  then run:

```bash
TAP_USERFLOW_AUTH_TOKEN='<your-token-here>' poetry run pytest
```

You can also test the `tap-userflow` CLI interface directly using `poetry run`:

```bash
poetry run tap-userflow --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

<!--
Developer TODO:
Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any "TODO" items listed in
the file.
-->

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-userflow
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-userflow --version
# OR run a test `elt` pipeline:
meltano elt tap-userflow target-jsonl
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to
develop your own taps and targets.
