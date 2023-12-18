"""
System Configuration Module
===========================

This package contains the modules for the system configuration.
Each configuration is a module. Modules can import one another to re-use
constants across multiple configurations, so that each specific configuration
only has to contain the constants that are unique to it.

`oncolysis_ctl/config` is the main module for the system configuration, which
invokes the modules found here.
"""