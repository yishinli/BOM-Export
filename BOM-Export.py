# -*- coding: UTF-8 -*
#Author-Kevin Schneider kevin.schneider@autodesk.com
#Author-Yishin Li ysli@araisrobo.com
#Description-BOM Export as cvs file
import adsk.core, adsk.fusion, traceback, os, gettext
commandIdOnPanel = 'Create BOM'
showversion = True #show versions in xref component names, default is off
docname = 'FOO' # a default name

# global set of event handlers to keep them referenced for the duration of the command
handlers = []

# Defines the location of the command to be in the DESIGN workspace and 
# in the CREATE panel below the Pipe command. See the user manual topic
# on "User Interface Customization" for details on how to get these ID's.
# https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
CMD_ID = commandIdOnPanel

# Support localization
_ = None
def getUserLanguage():
    app = adsk.core.Application.get();
    
    return {
        adsk.core.UserLanguages.ChinesePRCLanguage: "zh-CN",
        adsk.core.UserLanguages.ChineseTaiwanLanguage: "zh-TW",
        adsk.core.UserLanguages.CzechLanguage: "cs-CZ",
        adsk.core.UserLanguages.EnglishLanguage: "en-US",
        adsk.core.UserLanguages.FrenchLanguage: "fr-FR",
        adsk.core.UserLanguages.GermanLanguage: "de-DE",
        adsk.core.UserLanguages.HungarianLanguage: "hu-HU",
        adsk.core.UserLanguages.ItalianLanguage: "it-IT",
        adsk.core.UserLanguages.JapaneseLanguage: "ja-JP",
        adsk.core.UserLanguages.KoreanLanguage: "ko-KR",
        adsk.core.UserLanguages.PolishLanguage: "pl-PL",
        adsk.core.UserLanguages.PortugueseBrazilianLanguage: "pt-BR",
        adsk.core.UserLanguages.RussianLanguage: "ru-RU",
        adsk.core.UserLanguages.SpanishLanguage: "es-ES"
    }[app.preferences.generalPreferences.userLanguage]

# Get loc string by language
def getLocStrings():
    currentDir = os.path.dirname(os.path.realpath(__file__))
    return gettext.translation('resource', currentDir, [getUserLanguage(), "en-US"]).gettext 
    
def commandDefinitionById(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox(_('commandDefinition id is not specified'))
        return None
    commandDefinitions_ = ui.commandDefinitions
    commandDefinition_ = commandDefinitions_.itemById(id)
    return commandDefinition_

def commandControlByIdForQAT(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox(_('commandControl id is not specified'))
        return None
    toolbars_ = ui.toolbars
    toolbarQAT_ = toolbars_.itemById('QAT')
    toolbarControls_ = toolbarQAT_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

def destroyObject(uiObj, tobeDeleteObj):
    if uiObj and tobeDeleteObj:
        if tobeDeleteObj.isValid:
            tobeDeleteObj.deleteMe()
        else:
            uiObj.messageBox(_('tobeDeleteObj is not a valid object'))
            
# walk thru the assembly
def walkThrough(bom):
    parts = ''
    misc = ''
    bom = sorted(bom, key=lambda d: d['desc'])
    for item in bom:
        if (item['desc']):  # with descriptions for BOM
            parts += '"' + str(item['fullPathName']) + '","' + str(item['pn']) + '","' + str(item['desc']) + '",' + str(item['instances']) + '\n'
        else:               # without descriptions for CHECKING
            misc  += '"' + str(item['fullPathName']) + '","' + str(item['pn']) + '",' + str(item['instances']) + '\n'
    return (parts, misc)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        global _;
        _ = getLocStrings();
        
        commandName = _('Create BOM')
        commandDescription = _('Create BOM')
        commandResources = './resources'

        class CommandExecuteHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    command = args.firingEvent.sender
                    global docname
                    global showversion
                    
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    
                    design = app.activeProduct
                    docname = app.activeDocument.name

                    for input in inputs:
                        if input.id == 'docname_':
                            docname = input.value
                        elif input.id == 'showversion_':
                            showversion = input.value
                
                    # Make sure we have a desing
                    if not design:
                        ui.messageBox('A Design Must be Active.', 'BOM Export')
                        return
                        
                    # Get all occurrences in the root component of the active design
                    root = design.rootComponent
                    occs = root.allOccurrences # occurrences that includes sub-components

                    # Gather information about each unique component
                    bom = []
                    for occ in occs:
                        comp = occ.component
                        refocc = occ.isReferencedComponent
                        occtype = occ.childOccurrences.count
                        jj = 0
                        for bomI in bom:
                            if bomI['component'] == comp:
                                # Increment the instance count of the existing row.
                                bomI['instances'] += 1
                                break
                            jj += 1
            
                        if jj == len(bom):
                            # Modify the name if versions are OFF and an occurance is an xref
                            if (showversion == False and refocc == True):
                                longname = comp.name
                                shortname = " v".join(longname.split(" v")[:-1])
                            else:
                                shortname = comp.name
                                
                            mat = ''
                            bodies = comp.bRepBodies
                            for bodyK in bodies:
                                if bodyK.isSolid:
                                    mat += bodyK.material.name
                            
                            # Add this component to the BOM, only if it is with component.description
                            # if (comp.description):
                            bom.append({
                                'component': comp,
                                'fullPathName': occ.fullPathName,
                                'name': shortname,
                                'pn' : comp.partNumber,
                                'material' : mat,
                                'desc' : comp.description,
                                'instances': 1,
                                'sub': occtype,
                            })

                    (parts, misc) = walkThrough(bom)
                    # Display the BOM in the console
                    print ('\n')
                    print (docname + ' BOM\n')
                    print ('Full Path Name, ' + 'Part Number, ' + 'Description, ' + 'Count')
                    print (parts)
                    # title = ('Full Path Name, ' + 'Part Number, ' + 'Material, '+ 'Count')
                    # msg = title + '\n' + walkThrough(bom)
                    # ui.messageBox(msg, 'Bill Of Materials')
                     
                    # Display the BOM Save Dialog 
                    fileDialog = ui.createFileDialog()
                    fileDialog.isMultiSelectEnabled = False
                    fileDialog.title = "Save " + docname + " BOM as cvs"
                    fileDialog.initialDirectory = "c:/tmp"
                    fileDialog.initialFilename = docname
                    fileDialog.filter = 'Text files (*.csv)'
                    fileDialog.filterIndex = 0
                    dialogResult = fileDialog.showSave()
                    if dialogResult == adsk.core.DialogResults.DialogOK:
                        filename = fileDialog.filename
                    else:
                        return
                    
                    #Write the BOM    
                    output = open(filename, 'w', encoding='utf-8')
                    output.writelines(docname + ' BOM\n')
                    output.writelines('Full Path Name,' + 'Part Number,' + 'Description,' + 'Count\n')
                    output.writelines(parts)
                    output.close()            

                    index = filename.rfind('.csv')
                    if (index != -1):
                        misc_file = filename[:index] + '-MISC' + filename[index:]
                    else:
                        misc_file = filename + '-MISC.csv'
                    output = open(misc_file, 'w', encoding='utf-8')
                    output.writelines(docname + ' BOM\n')
                    output.writelines('Full Path Name,' + 'Part Number,' + 'Count\n')
                    output.writelines(misc)
                    output.close()            
                    
                    #confirm save
                    ui.messageBox( 'Document Saved to:\n' + filename, '', 0, 2)    
                    # command = args.firingEvent.sender
                    # ui.messageBox(_('command: {} executed successfully').format(command.parentCommandDefinition.id))
                except:
                    if ui:
                       ui.messageBox(_('command executed failed: {}').format(traceback.format_exc()))

        class CommandCreatedEventHandlerPanel(adsk.core.CommandCreatedEventHandler):
            def __init__(self):
                super().__init__() 
            def notify(self, args):
                try:
                    cmd = args.command
                    onExecute = CommandExecuteHandler()
                    cmd.execute.add(onExecute)
                    global docname
                    design = app.activeProduct
                    docname = app.activeDocument.name

                    # keep the handler referenced beyond this function
                    handlers.append(onExecute)
                    
                    commandInputs_ = cmd.commandInputs
                    commandInputs_.addStringValueInput('docname_', 'Title:', docname ) 
                    #dropDownCommandInput_ = commandInputs_.addDropDownCommandInput('BOMtype_', _('Drop Down'), adsk.core.DropDownStyles.LabeledIconDropDownStyle)
                    #dropDownItems_ = dropDownCommandInput_.listItems
                    #dropDownItems_.add(_('Parts only'), True)
                    #dropDownItems_.add(_('Indented Bom'), False)
                    #dropDownItems_.add(_('Top Level'), False)
                    #commandInputs_.addBoolValueInput('showversion_', 'Show Version', True, '', showversion)

                except:
                    if ui:
                        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        commandDefinitions_ = ui.commandDefinitions

        # add a command on create panel in modeling workspace
        workspaces_ = ui.workspaces
        modelingWorkspace_ = workspaces_.itemById('FusionSolidEnvironment')  # SOLID
        toolbarPanels_ = modelingWorkspace_.toolbarPanels
        toolbarPanel_ = toolbarPanels_.itemById('SolidCreatePanel') # SOLID.CREATE - add the new command under the second panel
        toolbarControlsPanel_ = toolbarPanel_.controls
        toolbarControlPanel_ = toolbarControlsPanel_.itemById(commandIdOnPanel)
        if not toolbarControlPanel_:
            commandDefinitionPanel_ = commandDefinitions_.itemById(commandIdOnPanel)
            if not commandDefinitionPanel_:
                commandDefinitionPanel_ = commandDefinitions_.addButtonDefinition(commandIdOnPanel, commandName, commandDescription, commandResources)
            onCommandCreated = CommandCreatedEventHandlerPanel()
            commandDefinitionPanel_.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            toolbarControlPanel_ = toolbarControlsPanel_.addCommand(commandDefinitionPanel_)
            toolbarControlPanel_.isVisible = True

    except:
        if ui:
            ui.messageBox(_('AddIn Start Failed: {}').format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        objArrayPanel = []

        # Gets the toolbar panel containing the button.
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        # Delete the button command control.
        cntrl = panel.controls.itemById(CMD_ID)
        if cntrl:
            cntrl.deleteMe()

        commandDefinitionPanel_ = commandDefinitionById(commandIdOnPanel)
        if commandDefinitionPanel_:
            objArrayPanel.append(commandDefinitionPanel_)

        for obj in objArrayPanel:
            destroyObject(ui, obj)
        
    except:
        if ui:
            ui.messageBox(_('AddIn Stop Failed: {}').format(traceback.format_exc()))
