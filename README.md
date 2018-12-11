# Scalafmt for Sublime Text 3

Sublime Text 3 plugin to invoke scalafmt, a code formatter for Scala.

## Requirements

- scalafmt (1.5.1): https://github.com/scalameta/scalafmt/tree/v1.5.1

- coursier (1.1.0): https://github.com/coursier/coursier

- nailgun client (0.9.1): https://github.com/facebook/nailgun/tree/nailgun-all-0.9.1

## Prerequisites

Create `scalafmt_ng` binary somewhere in your `PATH`, for instance in `/usr/local/bin`:

```
coursier bootstrap --standalone com.geirsson:scalafmt-cli_2.12:1.5.1 \
  -r bintray:scalameta/maven -o /usr/local/bin/scalafmt_ng \
  -f --main com.martiansoftware.nailgun.NGServer
```

Make sure you use the same version of nailgun in the client `ng` and the one packaged in `com.geirsson:scalafmt-cli`.

## Usage

Place a file `.scalafmt.conf` in your project folder. The file is searched from the folder containing the scala file to format down to the project root. When `.scalafmt.conf` is found in the directory tree, automatic formatting will be enabled on save.

The formatting can also be invoked from the sublime commands when the active file is recognized as a scala source file.

## Configuration

See https://scalameta.org/scalafmt/docs/configuration.html

## Remarks

The nailgun daemon is started the first time a formatting is requested. This can take a bit of time depending the machine and workload.

Once the daemon is running, next formatting task should execute faster.

The daemon is automatically shutdown when the plugin is reloaded, uninstalled or the editor is closed.
