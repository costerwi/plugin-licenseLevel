#!/bin/python

from abaqus import session, milestone
import customKernel
from licenseLevel import dslsstat

def updateCustomData():
    "Update CAE 'licenseFeatures' custom data"
    milestone(message='Collecting data from license server')
    licenseFeatures = session.customData.licenseFeatures
    licenseFeatures.clear()
    if hasattr(session, 'isFlexnet') and session.isFlexnet:
        licenseFeatures['error'] = "Sorry, the Flexnet license system is not yet supported.\n" \
            "Please consider upgrading to cloud hosted Managed DSLS at no additional cost."
        return
    try:
        licenseFeatures.update(dslsstat())
    except Exception as E:
        licenseFeatures['error'] = str(E)

session.customData.licenseFeatures = {}
