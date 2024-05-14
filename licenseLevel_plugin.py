"""Abaqus CAE plugin to report current Abaqus DSLS license usage

Usage:
    From the Abaqus CAE Job module, select Plug-ins->License level...

Carl Osterwisch, May 2024
"""

from abaqusGui import *
import abaqusGui
from kernelAccess import session
import sys

__version__ = "1.0.2"

# List of Abaqus features to report. Note: license trigram must be the first word
features = (
    'QAT solver tokens for Abaqus only\tAbaqus "Analysis" licenses',
    'QPT tokens for either Abaqus CAE or Abaqus solver\tAbaqus "Portfolio" licenses',
    'QXT solver tokens for Abaqus, fe-safe, Tosca, Isight\tSimulia "Extended" solver licenses',
    'SRU solver tokens for above plus CST, Simpack, PowerFLOW\tSimulia universal "SimUnit" solver licenses',
    'SUN solver credits for above plus CST, Simpack, PowerFLOW\tSimulia pre-paid consumable "SimUnit" solver licenses',
    'QAX tokens for Abaqus CAE, fe-safe GUI, Isight Gateway\tAbaqus "Extended" graphical user interface licenses',
)

###########################################################################
# Dialog box
###########################################################################
class licenseLevelDB(AFXDataDialog):
    """The license usage dialog box class
    """

    def __init__(self, form):
        # Construct the base class.
        AFXDataDialog.__init__(self,
                mode=form,
                title="Abaqus License Level",
                opts=DIALOG_NORMAL|DECOR_RESIZE)

        self.appendActionButton(text='Refresh', tgt=self, sel=self.ID_LAST)
        self.appendActionButton(self.DISMISS)
        FXMAPFUNC(self, SEL_COMMAND, self.ID_LAST, licenseLevelDB.updateData)

        self.progress = {}  # holds progress widgets
        p = FXGroupBox(self, 'Available licenses', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        p = AFXVerticalAligner(p, opts=LAYOUT_FILL_X)
        for feature in features:
            h = FXHorizontalFrame(p)
            FXLabel(h, feature, opts=LABEL_NORMAL|LAYOUT_SIDE_LEFT).setJustify(JUSTIFY_LEFT)
            trigram, _ = feature.split(' ', 1)
            self.progress[trigram] = AFXProgressBar(h,
                opts=LAYOUT_FIX_WIDTH|LAYOUT_FIX_HEIGHT|AFXPROGRESSBAR_ITERATOR, 
                w=200, h=22)
            if trigram in ('QAT', 'QPT'):
                h.hide()  # hide deprecated tokens unless they are available on server

        p = FXGroupBox(self, 'Usage details', opts=FRAME_GROOVE|LAYOUT_FILL_X|LAYOUT_FILL_Y)
        self.text = FXText(p,
            opts=LAYOUT_FILL_X|LAYOUT_FILL_Y|TEXT_READONLY|TEXT_WORDWRAP,
            w=300, h=300)


    def updateData(self, sender=None, sel=None, ptr=None):
        "Query the latest license info"
        sendCommand("licenseLevel_kernel.updateCustomData()", False)
        licenseFeatures = session.customData.licenseFeatures
        details = []
        error = licenseFeatures.get('error')
        if error:
            details.append(error)
        for feature in features:
            trigram, _ = feature.split(' ', 1)
            progress = self.progress.get(trigram)
            progress.setTotal(0) # default to 0
            progress.setProgress(0)
            data = licenseFeatures.get(trigram)
            if data is None:
                continue
            progress.getOwner().show() # make sure it's visible
            total = data.get('number', 0)
            progress.setTotal(total)
            progress.setProgress(total - data.get('inuse', 0))
            usage = data.get('usage')
            if usage:
                details.append(trigram)
                details.extend('\t' + line for line in usage)
        legacy = [trigram for trigram in ('QAT', 'QPT', 'QXT') if trigram in licenseFeatures]
        simunit = [trigram for trigram in ('SRU', 'SUN') if trigram in licenseFeatures]
        if legacy and simunit:
            details.append('\nNote: You have a mixture of solver license models. '
                'Specify license_model=LEGACY to use {}, licence_model=AUTOMATIC (default) to use {}.'
                .format(' or '.join(legacy), ' or '.join(simunit)))
        details = '\n'.join(details)
        if sys.version_info.major < 3: # Abaqus CAE < 2024
            details = details.encode('latin1', 'ignore')
        self.text.setText(details)


    def show(self):
        "Prepare to show the dialog box"
        self.updateData()
        return AFXDataDialog.show(self)


###########################################################################
# Form definition
###########################################################################
class licenseLevelForm(AFXForm):
    "Class to launch the dialog box"
    def __init__(self, owner):
        AFXForm.__init__(self, owner) # Construct the base class.

    def getFirstDialog(self):
        return licenseLevelDB(self)


###########################################################################
# Register abaqus plugin
###########################################################################
toolset = getAFXApp().getAFXMainWindow().getPluginToolset()

toolset.registerGuiMenuButton(
        buttonText='&License level...',
        object=licenseLevelForm(toolset),
        kernelInitString='import licenseLevel_kernel',
        author='Carl Osterwisch',
        version=__version__,
        applicableModules=['Job'],
        description='Report current DSLS license availability',
        helpUrl='https://github.com/costerwi/plugin-licenseLevel'
        )
