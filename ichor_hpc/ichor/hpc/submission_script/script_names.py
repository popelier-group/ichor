from pathlib import Path

# def prepend_script_directory(paths):
#     import ichor.hpc.global_variables

#     for key, val in paths.items():
#         if isinstance(val, dict):
#             paths[key] = prepend_script_directory(paths)
#         else:
#             paths[key] = ichor.hpc.global_variables.FILE_STRUCTURE["scripts"] / val
#     return paths


class ScriptNames(dict):
    """A helper class which returns the full path of a particular script that is used to submit job files
    for programs like Gaussian and AIMAll. All the script files are stored into a directory
    ichor.hpc.global_variables.FILE_STRUCTURE["scripts"].
    These scripts are submitted to compute nodes on CSF3/FFLUXLAB which initiates a job."""

    def __init__(
        self,
        script_names,
        parent: "FileStructure",  # noqa E821
        modify: str = "",
        **kwargs
    ):
        super().__init__(script_names, **kwargs)
        # parent directory
        self.script_names = script_names
        self.parent = parent
        self.modify = modify

    @property
    def file_structure(self):
        return self.script_names

    def __getitem__(self, item):
        """
        :param item: a key which corresponds to a particular script file value.
        See ichor.hpc.global_variables.SCRIPT_NAMES.
        """
        script = super().__getitem__(
            item
        )  # call dict __getitem__ method to get the script name (the value corresponding to the given key)
        # if an ichor script, you have to do ichor.hpc.global_variables.SCRIPT_NAMES["ichor"]["gaussian"] as
        # ichor.hpc.global_variables.SCRIPT_NAMES["ichor"] returns a ScriptNames type object
        # then the second time this object is indexed with ["gaussian"], it will
        # be an instance of "str", so this if statement will be executed
        if isinstance(script, (str, Path)):
            # append the script name to the path where the scripts are
            # located and modify script name with self.modify
            return self.parent / (script + self.modify)
        else:
            return script
