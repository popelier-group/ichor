from ichor.file_structure.node import FileNode


class FileTree(dict):
    """A dictionary that contains key:value pairs `_id`:FileNode(name,parent). This is the base class that the `FileStructure` class inherits from.
    See `FileStructure` for more details.
    """
    def add(self, name: str, _id: str, parent: str = None) -> None:
        """
        Adds a new key:value pair of _id:FileNode(name) to the file structure of ICHOR.
      
        For example doing: `self.add("SAMPLE_POOL", "sample_pool")` would add a key:value pair with key=sample_pool and value=FileNode(SAMPLE_POOL)
        If a parent directory exists, then `self.add("SAMPLE_POOL", "sample_pool", parent="PARENT_DIR_NAME")` will give a key:value pair with
        key=`sample_pool` and value=`FileNode(SAMPLE_POOL, "PARENT_DIR_NAME")`
        """
        if parent is not None:
            parent = super().__getitem__(parent)
        self[_id] = FileNode(name, parent)

    def __getitem__(self, _id) -> 'Path':
        """ Get the Path corresponding to the given _id

        :param _id: A string used as a key, whose cossesponding value is a Path object. Example: `training_set` key returns the `TRAINING_SET` directory path
        """
        return super().__getitem__(_id).path
