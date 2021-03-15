from ichor.file_structure.node import FileNode


class FileTree(dict):
    def add(self, name, _id, parent=None):
        if parent is not None:
            parent = super().__getitem__(parent)
        self[_id] = FileNode(name, parent)

    def __getitem__(self, _id):
        return super().__getitem__(_id).path
