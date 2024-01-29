from pathlib import Path
from typing import List, Union

from ichor.core.files import PointsDirectory
from ichor.core.files.directory import Directory


# note the inheritance order, because __iter__ will find the list __iter__ first...
class PointsDirectoryParent(list, Directory):
    """
    Should wrap around multiple PointsDirectory-ies.

    """

    _suffix = ".pointsdirparent"

    def __init__(self, path: Union[Path, str]):

        list.__init__(self)
        Directory.__init__(self, path)

    def _parse(self):
        """
        Called from Directory.__init__(self, path)
        Parse a directory (such as TRAINING_SET, TEST_SET,etc.)
        and make PointDirectory objects of each of the subirectories.
        If however there are only .gjf files present in the directory at the moment,
        then make a new directory for each .gjf file and move the .gjf file in there. So for example,
        if there is a file called WATER001.gjf, this method will make a folder called WATER001
        and will move WATER001.gjf in it.
        Initially when the training set, test set, and sample pool directories are made,
        there are only .gjf files present in the
        directory. This method makes them in separate directories.
        """

        # iterdir sorts by name, see Directory class
        for f in self.iterdir():
            # if the current PathObject is a directory that matches
            # a PointDirectory instance and add to self
            if PointsDirectory.check_path(f):
                pointsdir = PointsDirectory(f)
                self.append(pointsdir)

        # wrap the new directory as a PointDirectory instance and add to self
        # sort by the names of the directories (by the numbers in their name)
        # since the system name is always the same
        self = self.sort(key=lambda x: x.path.name)

    def write_to_json_database(
        self,
        root_name: str = None,
        npoints_per_json=500,
        print_missing_data=True,
        indent: int = 2,
        separators=(",", ":"),
    ) -> List[Path]:
        """Makes a database from multiple PointsDirectory-like directories which
        are contained in this PointsDirectoryParent

        :param root_name: The name of the database. If not selected, uses the name of the current
        PointsDirectoryParent, defaults to None
        :param npoints_per_json: Number of json files in each sub-directory, defaults to 500
        :param print_missing_data: Whether or not to print missing data, defaults to True
        :param indent: json file indent, defaults to 2
        :param separators: json file separators, defaults to (",", ":")
        """

        if not root_name:
            root_name = self.name_without_suffix

        # make the parent database json folder because there are potentially
        # going to be multiple json directories inside
        db_parent_dir = Path(f"{root_name}_json_parent")
        db_parent_dir.mkdir(exist_ok=False)

        root_paths = []

        for idx, pointdir in enumerate(self):
            root_path = pointdir.write_to_json_database(
                db_parent_dir / f"{root_name}{idx}",
                npoints_per_json=npoints_per_json,
                print_missing_data=print_missing_data,
                indent=indent,
                separators=separators,
            )
            root_paths.append(root_path)

        return root_paths

    def write_to_sqlite3_database(
        self, db_path: Union[str, Path] = None, echo=False, print_missing_data=True
    ) -> Path:
        """
        Write out important information from a PointsDirectory instance to an SQLite3 database.
        All PointsDirectory-like directories contained inside will be written to the same database

        :param db_path: database to write to
        :param echo: Whether to print out SQL queries from SQL Alchemy, defaults to False
        :param print_missing_data: Whether to print out any missing data from each PointDirectory contained
            in self, defaults to False
        :return: The path to the written SQL database
        """

        if not db_path:
            db_path = Path(f"{self.name_without_suffix}_parent.sqlite")
        else:
            db_path = Path(db_path).with_suffix(".sqlite")

        for pointsdir in self:

            # write all data to a single database by passing in the same name for every PointsDirectory
            # get the method and pass in the database path name
            pointsdir.write_to_sqlite3_database(
                db_path, echo=echo, print_missing_data=print_missing_data
            )
