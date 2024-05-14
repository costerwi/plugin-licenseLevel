# plugin-licenseLevel
Abaqus CAE plugin to display current DSLS license feature availability

## How it works
This plugin simply runs the following command and summarizes the results:

```
abaqus licensing dslsstat -usage
```

Only license features appropriate to the Abaqus graphical user interface or solver are displayed.
Other features like Catia are ignored.

Beware: It can take up to a minute to collect license usage information from online servers with several unique features.

Unfortunately, Flexnet license usage data is not yet supported.
Please consider upgrading to online Managed DSLS at no additional cost.

## Installation instructions

1. Download and unzip the [latest version](https://github.com/costerwi/plugin-licenseLevel/releases/latest)
2. Either double-click the included `install.cmd` or manually copy files into your abaqus_plugins directory
3. Restart Abaqus CAE and you will find `License level...` in the Job module plug-ins menu
