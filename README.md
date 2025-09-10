# Schedrem

A cross-platform task scheduler and reminder configured in YAML.

## How it Works

Schedrem is a Python package that provides a tool for scheduling tasks and setting reminders.

As a resident program, it monitors changes in the configuration file, triggers tasks to execute commands or display message boxes as reminders. It also validates the configuration format every time the file is saved.

The configuration file, which is a YAML file, is easy to read and write. You can use your favorite text editor to configure your schedules.

Audible alarm using a sound file (currently WAV format only) is available.

## Installation

Python 3.11 or later is required.

### From PyPI

Install from [PyPI](https://pypi.org/project/schedrem/) using `pip`:

```sh
python -m pip install -U schedrem
```

### From Source Using pip

```sh
git clone https://github.com/hikyae/schedrem
cd schedrem
python -m pip install -e .
```

### From AUR

There also exists an [AUR](https://aur.archlinux.org/packages/schedrem) package.

Install from AUR using a helper such as `yay` or `paru`:

```sh
yay -S schedrem
```

```sh
paru -S schedrem
```

#### From Source Using Makepkg

```sh
git clone https://aur.archlinux.org/schedrem.git
cd schedrem
makepkg -si
```

## Configuration

Schedrem searches for the configuration file in the order specified below and uses the first one that is found. The actual path depends on the platform and environment variables.

The file must be in YAML format. Edit it with your preferred text editor, and make sure it is encoded in UTF-8.

Schedrem will automatically detect the changes you've made to the configuration file. If there is an error in the file, a message box will pop up and it will try to tell you the reason. Please fix the file and save it, then close the message box. Otherwise, the message box will keep popping up.

Note that there is no configuration file to set **command-line options** such as `--config` or `--debug`.

### Path Specified by Command-Line Parameter

You can set the file path by passing it as a command-line parameter:

```sh
schedrem --config path/to/config
```

### Default Paths for Linux/macOS

- `${XDG_CONFIG_HOME}/schedrem/config.yml`
- `${XDG_CONFIG_HOME}/schedrem/config.yaml`
- `${HOME}/.config/schedrem/config.yml`
- `${HOME}/.config/schedrem/config.yaml`

### Default Paths for Windows

- `%USERPROFILE%\.config\schedrem\config.yml`
- `%USERPROFILE%\.config\schedrem\config.yaml`
- `%APPDATA%\schedrem\config.yml`
- `%APPDATA%\schedrem\config.yaml`

### Examples

Please refer to the [examples](https://github.com/hikyae/schedrem/tree/main/examples) directory in this repository.

### Structure

#### Schedules

All the schedules should be listed here.

Each schedule is an item in the list of `schedules`, denoted by a leading hyphen (-).
It can have `description` (abbreviated as `desc`), `time`, `wait`, `delay`, `enabled`, and an action that consists of `message` (abbreviated as `msg`), `yesno`, `command` (abbreviated as `cmd`), `sound`, and `font`.
Basically, every key is optional with a few exceptions. If there is no action specified out of `message`, `yesno`, or `command`, an error occurs.

```yaml
schedules:
  - message: This is the simplest schedule. This message is shown every minute.

  - description: The message "Good morning" is shown every day at 6 o'clock.
    time:
      hour: 6
      minute: 0
    message: Good morning.
```

##### Description

A string to describe the schedule.

##### Time

The time specification is inspired by cron, but is more readable and has some differences.

Specify integers or a list of integers for `year`, `month`, `day`, `hour`, `minute` to schedule the date(s) and time(s).
Specify string or a list of strings for `weekday` (abbreviated as `dow`) to schedule the day(s) of the week.

If you omit any of them, then the task is triggered at any of the times within that range. This is similar to using `*` in a crontab.

If you don't specify the time, then the task is triggered every minute.

##### Wait

The time to wait before triggering the task. The task won't be triggered until the specified time has elapsed.

You can specify integers for `year`, `month`, `day`, `hour`, `minute`, but only `year` is mandatory.

##### Delay

Additional delay to be applied to each scheduled time. You can specify a non-negative float value in seconds. The default is `0.0`.

This was implemented as a workaround to mitigate a bug in certain desktop environments where some message boxes fail to appear when multiple ones are created simultaneously.

##### Enabled

A boolean (`true`/`false`, `yes`/`no`, `on`/`off`) to set whether the task should be triggered or not. The default value is `true`.

Useful when you toggle multiple schedules with a single flag using an anchor in YAML.

##### Action

The "action" is a conceptual term, not a configuration file key. The configuration file consists of the following keys: `message` (abbreviated as `msg`), `yesno`, `command` (abbreviated as `cmd`), `sound`, and `font`.

The detail of these keys is as follows:

- `message`: A string to show in a message box with an OK button.
- `yesno`: A string to display in a message box asking for a Yes or No response. If the user selects "Yes", the `command` will be executed, and the `message` will be shown if they are specified. If "No" is selected, neither the `command` nor the `message` will be run.
- `command`: A string of an arbitrary shell command.
- `sound`: A string of the path to a sound file to play, or a boolean (`true`/`false`, `yes`/`no`, `on`/`off`) to set whether the default sound should be played while showing a message box. The only acceptable sound file format is WAV.
- `font`: A string specifying the font family and font size to use in the message box, in the format `<font family> <font size>`, for example, "Cica 40". This option is currently not available on Windows.

#### Optional global settings

These are optional settings that affect all schedules.

- `disabled`: A boolean (`true`/`false`, `yes`/`no`, `on`/`off`) to set whether Schedrem should run or not. Set this to `true` when you want Schedrem to stop waiting for all schedules or when you want all running tasks, including all visible message boxes, to be killed. The default value is `false`.

  ```yaml
  disabled: true
  ```

- `weekdaynames`: A list of lists of strings to set the names for the days of the week. They start from Monday and are case-insensitive. The default value is `[mon, tue, wed, thu, fri, sat, sun]`.

  ```yaml
  weekdaynames:
    - [mon, tue, wed, thu, fri, sat, sun]
    - [月, 火, 水, 木, 金, 土, 日]

  schedules:
    - description: Time to take out the burnable trash
      time:
        hour: 7
        minute: 50
        weekday: 月
      message: 燃えるゴミを捨てる
  ```

- `font`: A string specifying the font family and font size to use in the message box, in the format `<font family> <font size>`, for example, "Cica 40". If you set this value outside of `schedules`, each action will use this font setting unless the font is explicitly set within the action. The default value is `Arial 19`. This option is currently not available on Windows.

  ```yaml
  font: Arial 70

  schedules:
    - description: You will see the huge text every minute
      message: HUGE
  ```

- `aliases`: Thanks to the YAML specification, it is possible to make aliases for values for schedules. The naming of the key `aliases` is not mandatory.

```yaml
aliases:
  - &workdays [mon, tue, wed, thu, fri]
  - &friday13th
    day: 13
    dow: fri

schedules:
  - desc: Time to go
    time:
      hour: 8
      minute: 0
      dow: *workdays
    msg: Go to work

  - desc: Beware of unluckiness in the morning
    time:
      hour: 8
      minute: 0
      <<: *friday13th
    msg: Good morning, and beware!
```

## Usage

First, you need to put your configuration file into one of the places described in the [Configuration](#configuration) section.

Try starting Schedrem from a terminal to check for any errors:

```sh
schedrem --debug
```
> [!WARNING]
> On Windows, the installed `schedrem` command runs in the background and does not display any output in the command prompt. Instead, execute the following command to check the output from schedrem.
```sh
python -m schedrem --debug
```

This starts Schedrem in the foreground with the debug option, displaying configuration information if there are no issues. If no errors appear, you're good to proceed. You can stop the process by pressing `<Ctrl>+C`.

Set the config path if you put it besides the defaults:

```sh
schedrem --config path/to/config
```

### Auto-starting

On Linux, to start Schedrem as a background program in a stand-alone window manager, add the following line to your startup script, such as `~/.xinitrc`:

```sh
schedrem &
```

The trailing ampersand "&" means that the program should run in the background. To stop Schedrem, just type `pkill schedrem`.

In a desktop environment (such as GNOME, KDE, Xfce, MATE, Cinnamon, etc.), you can simply add Schedrem to the list of autostarted applications without the trailing "&".

On Windows, you need to create a shortcut for the command:

1. Open the Startup Folder:
    - Press Win + R, type `shell:startup`, and press Enter.

2. Create a New Shortcut:
    - Right-click inside the Startup folder and select New > Shortcut.

3. Enter the Shortcut Target:
    - In the location field, type `schedrem`. Its absolute path will be resolved automatically.
    - Click **Next**.

4. Name the Shortcut:
    - Enter `schedrem` as the name.
    - Click **Finish**.

On macOS, you need to put a plist file as `~/Library/LaunchAgents/com.yourusername.schedrem.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourusername.schedrem</string>
    <key>ProgramArguments</key>
    <array>
        <string>schedrem</string> <!-- Assuming "schedrem" is accessible via PATH -->
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

## Tips

- There is a command-line option `--action` that can receive a JSON string as an action.
Though this option is used internally for executing tasks, you can also manually execute it as a command. Answering "No" to yesno prompt lets the command exit with the code 1. If `command` is specified and executed, the command exits with its return code.

```sh
schedrem --action '{"msg":"test","sound":true}'
schedrem --action '{"yesno":"yes?","cmd":"echo yes"}'; echo $?
schedrem --action '{"yesno":"Did you do push-ups?","msg":"Nice."}' || schedrem --action '{"msg":"Do it."}'
# Snoozeable alarm example in a Unix shell
while ! schedrem --action '{"yesno":"wake up","sound":true}'; do sleep 5m; done
```

- Unlike cron, you can configure the time with constraints on both the day of the month **and** the day of the week.
