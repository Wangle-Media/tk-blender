import bpy
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class BlenderRoyalRenderPublishPlugin(HookBaseClass):
    """
    Publish plugin that submits the current Blender session to Royal Render.

    Requires rrSubmit_Blender_1+.py to be present in Blender's startup scripts
    directory so that the royalrender.submitscene operator is registered.
    """

    @property
    def name(self):
        return "Submit to Royal Render"

    @property
    def description(self):
        return (
            "Submits the scene to Royal Render via rrSubmitter. "
            "The rrSubmitter UI will open so you can review and confirm the job "
            "before it is queued. Requires rrSubmit_Blender_1+.py to be installed "
            "in Blender's startup scripts."
        )

    @property
    def item_filters(self):
        return ["blender.session"]

    @property
    def settings(self):
        return {}

    def accept(self, settings, item):
        if not hasattr(bpy.ops, "royalrender") or not hasattr(
            bpy.ops.royalrender, "submitscene"
        ):
            self.logger.debug(
                "royalrender.submitscene operator not registered — "
                "rrSubmit_Blender_1+.py may not be installed in Blender's startup scripts."
            )
            return {"accepted": False}

        return {"accepted": True, "checked": False}

    def validate(self, settings, item):
        if not bpy.data.filepath:
            self.logger.error(
                "The scene must be saved to disk before submitting to Royal Render."
            )
            return False

        return True

    def publish(self, settings, item):
        self.logger.info(
            "Launching rrSubmitter for: %s" % bpy.data.filepath
        )

        result = bpy.ops.royalrender.submitscene()

        if "FINISHED" not in result:
            self.logger.error(
                "Royal Render submission operator returned: %s" % result
            )
            return False

        self.logger.info("rrSubmitter launched successfully.")
        return True

    def finalize(self, settings, item):
        pass
