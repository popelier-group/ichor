from ichor.logging import logger


def submit_gjfs(directory):
    logger.info("Submitting gjfs to Gaussian")
    gjfs = Set(directory).read_gjfs()
    gjfs.format_gjfs()
    return gjfs.submit_gjfs()
