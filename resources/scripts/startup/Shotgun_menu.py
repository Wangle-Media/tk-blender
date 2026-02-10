# ----------------------------------------------------------------------------
# Copyright (c) 2020, Diego Garcia Huerta.
#
# Your use of this software as distributed in this GitHub repository, is
# governed by the Apache License 2.0
#
# Your use of the Shotgun Pipeline Toolkit is governed by the applicable
# license agreement between you and Autodesk / Shotgun.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------


import os
import sys
import imp
import time
import ast
import inspect
import subprocess
import importlib

import bpy
from bpy.types import Header, Menu, Panel, Operator
from bpy.app.handlers import load_factory_startup_post, persistent

import site

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

ext_libs = os.environ.get("PYSIDE2_PYTHONPATH")

if ext_libs and os.path.exists(ext_libs):
    if ext_libs not in sys.path:
        print("Added path: %s" % ext_libs)
        site.addsitedir(ext_libs)

bl_info = {
    "name": "Shotgun Bridge Plugin",
    "description": "Shotgun Toolkit Engine for Blender",
    "author": "Diego Garcia Huerta",
    "license": "GPL",
    "deps": "",
    "version": (1, 0, 0),
    "blender": (2, 82, 0),
    "location": "Shotgun",
    "warning": "",
    "wiki_url": "https://github.com/diegogarciahuerta/tk-blender/releases",
    "tracker_url": "https://github.com/diegogarciahuerta/tk-blender/issues",
    "link": "https://github.com/diegogarciahuerta/tk-blender",
    "support": "COMMUNITY",
    "category": "User Interface",
}


def _try_install_pyside6():
    """
    Attempt to automatically install PySide6 into Blender's Python environment.
    
    Returns:
        bool: True if installation succeeded or PySide6 is now importable, False otherwise.
    """
    import site  # Import at function level to avoid scope issues
    
    print("=" * 80)
    print("SHOTGUN TOOLKIT: PySide6 not found, attempting auto-installation...")
    print(f"Python executable: {sys.executable}")
    print("=" * 80)
    
    # First, check if pip is available
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print("pip is not available. Attempting to install pip using ensurepip...")
            result = subprocess.run(
                [sys.executable, "-m", "ensurepip", "--default-pip"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print(f"Failed to install pip: {result.stderr}")
                return False
            print("pip installed successfully.")
    except Exception as e:
        print(f"Error checking/installing pip: {e}")
        return False
    
    # Now try to install PySide6
    try:
        print("Installing PySide6 to user-local directory (this may take 1-2 minutes)...")
        
        # Install to user site-packages (doesn't require admin rights)
        result = subprocess.run(
            [
                sys.executable, "-m", "pip", "install", "PySide6",
                "--user", "--upgrade", "--no-warn-script-location"
            ],
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout for larger package
        )
        
        if result.returncode == 0:
            print("=" * 80)
            print("PySide6 installation completed successfully!")
            
            # Get the user site-packages directory
            user_site = site.getusersitepackages()
            print(f"Installed to user directory: {user_site}")
            
            # Ensure user site-packages is in sys.path
            if user_site not in sys.path:
                sys.path.insert(0, user_site)
                print(f"Added {user_site} to sys.path")
            
            print("Invalidating import caches and refreshing sys.path...")
            
            # Invalidate import caches so Python can find the newly installed package
            importlib.invalidate_caches()
            
            # Refresh site packages to update sys.path
            importlib.reload(site)
            
            print(f"Updated sys.path: {sys.path[:3]}...")  # Show first 3 entries
            print("=" * 80)
            return True
        else:
            print("=" * 80)
            print(f"PySide6 installation failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            print("=" * 80)
            return False
    except subprocess.TimeoutExpired:
        print("PySide6 installation timed out after 3 minutes.")
        return False
    except Exception as e:
        print(f"Error during PySide6 installation: {e}")
        return False


PYSIDE2_MISSING_MESSAGE = (
    "\n"
    + "-" * 80
    + "\nCould not import PySide2 or PySide6 as a Python module. Shotgun menu will not be available."
    + "\n\nAuto-installation was attempted but failed. Please install manually:"
    + "\n  Blender Python: python -m pip install PySide6 --user"
    + "\n\nFor more information, check the engine documentation:"
    + "\nhttps://github.com/diegogarciahuerta/tk-blender/edit/master/README.md\n"
    + "-" * 80
)

PYSIDE2_IMPORTED = False
PYSIDE6_IMPORTED = False

print("Shotgun Toolkit: Checking for PySide2/PySide6...")

# Try importing PySide2 first
try:
    from PySide2 import QtWidgets, QtCore
    PYSIDE2_IMPORTED = True
    print("Shotgun Toolkit: PySide2 imported successfully.")
except (ImportError, ModuleNotFoundError) as e:
    print(f"Shotgun Toolkit: PySide2 not available - {e}")
    PYSIDE2_IMPORTED = False

# If PySide2 failed, try PySide6
if not PYSIDE2_IMPORTED:
    print("Shotgun Toolkit: Attempting to import PySide6...")
    try:
        from PySide6 import QtWidgets, QtCore
        PYSIDE6_IMPORTED = True
        print("Shotgun Toolkit: PySide6 imported successfully.")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"Shotgun Toolkit: PySide6 not available - {e}")
        # Both failed - attempt auto-installation of PySide6
        if _try_install_pyside6():
            # Retry import after installation
            try:
                from PySide6 import QtWidgets, QtCore
                PYSIDE6_IMPORTED = True
                print("=" * 80)
                print("SUCCESS: PySide6 is now available. Shotgun menu will load.")
                print("=" * 80)
            except (ImportError, ModuleNotFoundError) as e:
                print(f"Failed to import PySide6 even after installation: {e}")

# Final status
if not PYSIDE2_IMPORTED and not PYSIDE6_IMPORTED:
    print("=" * 80)
    print("WARNING: Neither PySide2 nor PySide6 could be loaded.")
    print("Shotgun menu WILL NOT be available in Blender.")
    print("Check the output above for error details.")
    print("=" * 80)
else:
    print("Shotgun Toolkit: Qt bindings available, menu will be created.")



class ShotgunConsoleLog(bpy.types.Operator):
    """
    A simple operator to log issues to the console.
    """

    bl_idname = "shotgun.logger"
    bl_label = "Shotgun Logger"

    message: bpy.props.StringProperty(name="message", description="message", default="")

    level: bpy.props.StringProperty(name="level", description="level", default="INFO")

    def execute(self, context):
        self.report({self.level}, self.message)
        return {"FINISHED"}


# based on
# https://github.com/vincentgires/blender-scripts/blob/master/scripts/addons/qtutils/core.py
class QtWindowEventLoop(bpy.types.Operator):
    """
    Integration of qt event loop within Blender
    """

    bl_idname = "screen.qt_event_loop"
    bl_label = "Qt Event Loop"

    def processEvents(self):
        if hasattr(self, '_event_loop') and self._event_loop:
            self._event_loop.processEvents()
        if hasattr(self, '_app') and self._app:
            self._app.sendPostedEvents(None, 0)

    def modal(self, context, event):
        if event.type == "TIMER":
            if hasattr(self, '_app') and self._app and not self.anyQtWindowsAreOpen():
                self.cancel(context)
                return {"FINISHED"}

            self.processEvents()
        return {"PASS_THROUGH"}

    def anyQtWindowsAreOpen(self):
        return any(w.isVisible() for w in QtWidgets.QApplication.topLevelWidgets())

    def execute(self, context):
        # Initialize instance attributes
        self._app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(
            sys.argv
        )
        self._event_loop = QtCore.QEventLoop()

        # run modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.001, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def cancel(self, context):
        """Remove event timer when stopping the operator."""
        if hasattr(self, '_timer') and self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)


class ShotgunMenuCommand(bpy.types.Operator):
    """
    Dynamically created operator for Shotgun commands
    """
    bl_idname = "shotgun.command"
    bl_label = "Shotgun Command"
    
    command_name: bpy.props.StringProperty(name="command_name")
    
    def execute(self, context):
        try:
            import sgtk
            engine = sgtk.platform.current_engine()
            
            if not engine:
                self.report({'ERROR'}, "Shotgun engine not available")
                return {'CANCELLED'}
            
            if self.command_name not in engine.commands:
                self.report({'ERROR'}, f"Command '{self.command_name}' not found")
                return {'CANCELLED'}
            
            callback = engine.commands[self.command_name].get('callback')
            if not callback:
                self.report({'ERROR'}, f"No callback for '{self.command_name}'")
                return {'CANCELLED'}
            
            print(f"SHOTGUN: Executing command '{self.command_name}'")
            callback()
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error executing command: {str(e)}")
            print(f"SHOTGUN COMMAND ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class TOPBAR_MT_shotgun(Menu):
    """
    Creates the Shotgun top level menu
    """

    bl_label = "Shotgun"
    bl_idname = "TOPBAR_MT_shotgun"

    def draw(self, context):
        print("=" * 80)
        print("SHOTGUN MENU: draw() function called!")
        print("=" * 80)
        
        layout = self.layout
        
        try:
            import sgtk
            engine = sgtk.platform.current_engine()
            
            if not engine:
                layout.label(text="Shotgun engine not initialized", icon='ERROR')
                print("SHOTGUN MENU: Engine not initialized yet")
                return
            
            # Add context info at the top
            ctx = engine.context
            layout.label(text=str(ctx), icon='INFO')
            layout.separator()
            
            # Get commands and sort them
            commands = engine.commands
            if not commands:
                layout.label(text="No commands available", icon='INFO')
                return
            
            menu_items = []
            for cmd_name, cmd_details in commands.items():
                menu_items.append({
                    'name': cmd_name,
                    'details': cmd_details
                })
            
            # Sort by name
            menu_items.sort(key=lambda x: x['name'])
            
            print(f"SHOTGUN MENU: Drawing {len(menu_items)} commands")
            
            # Add each command as an operator
            for item in menu_items:
                cmd_name = item['name']
                cmd_details = item['details']
                
                # Create operator call
                op = layout.operator(
                    "shotgun.command",
                    text=cmd_name
                )
                op.command_name = cmd_name
                
        except Exception as e:
            layout.label(text=f"Error: {str(e)}", icon='ERROR')
            print(f"SHOTGUN MENU ERROR: {e}")
            import traceback
            traceback.print_exc()


def insert_main_menu(menu_class, before_menu_class):
    """
    This function allows adding a new menu into the top menu bar in Blender,
    inserting it before another menu specified.

    In order to be changes proof, this function collects the code for the
    Operator that creates the top level menus, and modifies it by using
    python AST (Abstract Syntax Trees), finds where the help menu is appended,
    and inserts a new AST node in between that represents our new menu.

    Then it is a matter of registering the class for Blender to recreate it's
    own top level menus with the additional

    A bit overkill, but the alternative was to copy&paste some Blender original
    code that could have changed from version to version. (if fact it did
    change from minor version to minor version while developing this engine.)

    """

    # This is an AST nodetree that represents the following code:
    # layout.menu("<menu_class.__name__>")
    # which will ultimately be inserted before the menu specified.
    sg_ast_expr = ast.Expr(
        value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="layout", ctx=ast.Load()), attr="menu", ctx=ast.Load()
            ),
            args=[ast.Str(s=menu_class.__name__)],
            keywords=[],
        )
    )

    # get the source code for the top menu bar menus
    code = inspect.getsource(bpy.types.TOPBAR_MT_editor_menus)
    code_ast = ast.parse(code)

    # find the `draw` method
    function_node = None
    for node in ast.walk(code_ast):
        if isinstance(node, ast.FunctionDef) and node.name == "draw":
            function_node = node
            break

    # find where the help menu is added, and insert ours right before it
    for i, node in enumerate(function_node.body):
        if isinstance(node, ast.Expr) and before_menu_class.__name__ in ast.dump(node):
            function_node.body.insert(i - 1, sg_ast_expr)
            break

    # make sure line numbers are fixed
    ast.fix_missing_locations(code_ast)

    # compile and execute the code
    code_ast_compiled = compile(code_ast, filename=__file__, mode="exec")
    exec(code_ast_compiled)

    # the newly create class is now within the local variables
    return locals()["TOPBAR_MT_editor_menus"]


# class TOPBAR_MT_editor_menus(Menu):
#     """
#     I could not find an easy way to simply add the menu into Blender's top
#     menubar.

#     So we use a bit of a hack, by recreating the the same as what blender does
#     to create it's own top level menus but adding the `Shotgun` menu right
#     before `help` menu.

#     Note that If the script to generate those menus was to change in Blender,
#     this would have to be update to reflect the same changes!
#     """
#     bl_idname = "TOPBAR_MT_editor_menus"
#     bl_label = ""

#     def draw(self, _context):
#         layout = self.layout

#         layout.menu("TOPBAR_MT_app", text="", icon='BLENDER')

#         layout.menu("TOPBAR_MT_file")
#         layout.menu("TOPBAR_MT_edit")

#         layout.menu("TOPBAR_MT_render")

#         layout.menu("TOPBAR_MT_window")
#         layout.menu("TOPBAR_MT_shotgun")
#         layout.menu("TOPBAR_MT_help")


def boostrap():
    # start the engine
    SGTK_MODULE_PATH = os.environ.get("SGTK_MODULE_PATH")
    if SGTK_MODULE_PATH and SGTK_MODULE_PATH not in sys.path:
        sys.path.insert(0, SGTK_MODULE_PATH)

    engine_startup_path = os.environ.get("SGTK_BLENDER_ENGINE_STARTUP")
    
    # Note: The engine sets SHOTGUN_SKIP_QTWEBENGINEWIDGETS_IMPORT=1 on Windows
    # to handle QtWebEngine issues, so no monkey patching needed

    engine_startup = imp.load_source("sgtk_blender_engine_startup", engine_startup_path)

    # Fire up Toolkit and the environment engine.
    engine_startup.start_toolkit()


@persistent
def startup(dummy):
    bpy.ops.screen.qt_event_loop()
    boostrap()


@persistent
def error_importing_pyside2(*args):
    bpy.ops.shotgun.logger(level="ERROR", message=PYSIDE2_MISSING_MESSAGE)


def register():
    print("=" * 80)
    print("SHOTGUN ADDON: Starting registration...")
    print("=" * 80)
    
    bpy.utils.register_class(ShotgunConsoleLog)
    print("SHOTGUN ADDON: Registered ShotgunConsoleLog")

    if not PYSIDE2_IMPORTED and not PYSIDE6_IMPORTED:
        print("SHOTGUN ADDON: No Qt bindings available, skipping menu registration")
        # bpy.app.timers.register(error_importing_pyside2, first_interval=5)
        load_factory_startup_post.append(error_importing_pyside2)
        return

    bpy.utils.register_class(ShotgunMenuCommand)
    print("SHOTGUN ADDON: Registered ShotgunMenuCommand operator")
    
    bpy.utils.register_class(QtWindowEventLoop)
    print("SHOTGUN ADDON: Registered QtWindowEventLoop")
    
    TOPBAR_MT_help = bpy.types.TOPBAR_MT_help
    print(f"SHOTGUN ADDON: Found TOPBAR_MT_help: {TOPBAR_MT_help}")
    
    TOPBAR_MT_editor_menus = insert_main_menu(
        TOPBAR_MT_shotgun, before_menu_class=TOPBAR_MT_help
    )
    print(f"SHOTGUN ADDON: Created modified TOPBAR_MT_editor_menus")
    
    bpy.utils.register_class(TOPBAR_MT_editor_menus)
    print("SHOTGUN ADDON: Registered modified TOPBAR_MT_editor_menus")
    
    bpy.utils.register_class(TOPBAR_MT_shotgun)
    print("SHOTGUN ADDON: Registered TOPBAR_MT_shotgun menu class")
    
    print("=" * 80)
    print("SHOTGUN ADDON: Registration complete! Menu should be visible.")
    print("=" * 80)

    load_factory_startup_post.append(startup)


def unregister():
    bpy.utils.unregister_class(ShotgunConsoleLog)

    if not PYSIDE2_IMPORTED and not PYSIDE6_IMPORTED:
        return

    bpy.utils.unregister_class(TOPBAR_MT_shotgun)
    bpy.utils.unregister_class(ShotgunMenuCommand)
