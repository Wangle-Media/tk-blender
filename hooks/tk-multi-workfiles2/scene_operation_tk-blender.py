# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import os
import bpy

import sgtk
from sgtk.platform.qt import QtGui

__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the
    current scene
    """

    def _apply_render_path(self, context, file_path):
        """
        Resolve the render output template for the current context and
        set it on every scene in the file. Frame padding (####) is
        appended so RR and Blender's own renderer both pick up the
        correct per-frame filenames.
        """
        engine = sgtk.platform.current_engine()
        if not engine:
            return

        tk = engine.sgtk
        is_shot = context.entity and context.entity.get("type") == "Shot"

        if is_shot:
            work_tmpl_name = "blender_shot_work"
            render_tmpl_name = "blender_shot_render"
        else:
            work_tmpl_name = "blender_asset_work"
            render_tmpl_name = "blender_asset_render"

        try:
            work_template = tk.templates.get(work_tmpl_name)
            render_template = tk.templates.get(render_tmpl_name)
            if not work_template or not render_template:
                return

            fields = work_template.get_fields(file_path)
            fields.update(context.as_template_fields(render_template, validate=True))

            render_path = render_template.apply_fields(fields)
            os.makedirs(os.path.dirname(render_path), exist_ok=True)

            for scene in bpy.data.scenes:
                scene.render.filepath = render_path + "####"

            engine.logger.debug("Render path set to: %s####" % render_path)

        except Exception as e:
            engine.logger.warning("Could not set render path: %s" % e)

    def execute(
        self,
        operation,
        file_path,
        context,
        parent_action,
        file_version,
        read_only,
        **kwargs
    ):
        """
        Main hook entry point

        :param operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                                then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an empty
                                                 state, otherwise False
                                all others     - None
        """

        if operation == "current_path":
            return bpy.data.filepath

        elif operation == "open":
            bpy.ops.wm.open_mainfile(filepath=file_path)
            self._apply_render_path(context, file_path)

        elif operation == "save":
            bpy.ops.wm.save_mainfile("EXEC_AREA")

        elif operation == "save_as":
            bpy.ops.wm.save_mainfile(filepath=file_path)
            self._apply_render_path(context, file_path)

        elif operation == "reset":
            if bpy.data.is_dirty:
                # changes have been made to the scene
                res = QtGui.QMessageBox.question(
                    None,
                    "Save your scene?",
                    "Your scene has unsaved changes. Save before proceeding?",
                    QtGui.QMessageBox.Yes
                    | QtGui.QMessageBox.No
                    | QtGui.QMessageBox.Cancel,
                )

                if res == QtGui.QMessageBox.Cancel:
                    return False
                elif res == QtGui.QMessageBox.Yes:
                    scene_name = bpy.data.filepath
                    if not scene_name:
                        bpy.ops.wm.save_mainfile("INVOKE_AREA")
                    else:
                        bpy.ops.wm.save_mainfile(filepath=scene_name)

            # do new file:
            bpy.ops.wm.read_homefile()
            return True
