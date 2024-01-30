from ichor.core.files.file_data import HasData


def no_processing_function(obj: HasData) -> dict:
    """Processing function which just returns the raw data associated with the object.
    Useful if calling processed_data from a higher level object, but some data of objects
    do not require any processing.

    :param obj: HasData object instance
    :return: Returns the raw data associated with the object
    :rtype: _type_
    """

    return obj.raw_data
