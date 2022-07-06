"""
instantiates a "global" logger for all parsing related stuff
"""
import logging

parsing_logger = logging.getLogger("ahbicht.expressions")
parsing_logger.setLevel(logging.DEBUG)
